from flask import Flask, request, jsonify
import json
import urllib.request as urllib_request
import urllib.error as urllib_error
import os
import logging
import re
from typing import Tuple, List, Dict, Any
from collections import Counter
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("email_classifier")

# 配置
OLLAMA_MODEL = os.getenv('OLLAMA_MODEL', "rwkv-7-g1a:0.4b")
#OLLAMA_API_URL = os.getenv('OLLAMA_API_URL', "http://rwkv.linuxuser.site/api/generate")
# 使用本地部署的Ollama服务器
OLLAMA_API_URL = os.getenv('OLLAMA_API_URL', "http://127.0.0.1:11434/api/generate")
SERVER_HOST = os.getenv('SERVER_HOST', "0.0.0.0")
SERVER_PORT = int(os.getenv('SERVER_PORT', "8501"))

app = Flask(__name__)

class EmailClassifier:
    """基于规则和LLM的混合邮件分类器"""
    
    # 关键词和模式库
    SCAM_KEYWORDS = [
        '奖金', '中奖', '红包', '免费', '领取', '点击', '链接', '验证码', '密码', '账户',
        '幸运', '奖品', '兑换', '现金', '汇款', '转账', '付款', '投资', '收益', '理财',
        'urgent', 'prize', 'winner', 'free', 'click', 'link', 'password', 'account',
        'verify', 'payment', 'transfer', 'investment'
    ]
    
    AD_KEYWORDS = [
        '促销', '优惠', '打折', '特价', '限时', '购买', '销售', '推广', '广告', '商城',
        '新品', '上市', '预订', '折扣', '省钱', '省钱', '省钱', 'vip', '会员',
        'sale', 'discount', 'promotion', 'buy', 'shop', 'offer', 'deal', 'limited'
    ]
    
    NORMAL_KEYWORDS = [
        '会议', '工作', '报告', '项目', '安排', '计划', '通知', '提醒', '同事', '领导',
        '文档', '文件', '附件', '讨论', '问题', '解决', '进展', '更新', '反馈',
        'meeting', 'work', 'report', 'project', 'schedule', 'team', 'update', 'feedback'
    ]
    
    # IP/端口测试模式
    TEST_PATTERNS = [
        r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b',  # IP地址
        r'port\s+\d+',  # 端口
        r'test\s+mail',  # 测试邮件
        r'smtp', 'pop3', 'imap'  # 邮件协议
    ]

    def __init__(self):
        self.rule_weights = {
            'keyword_match': 0.4,
            'pattern_match': 0.3,
            'length_analysis': 0.1,
            'llm_analysis': 0.2
        }

    def keyword_analysis(self, text: str) -> Tuple[float, float, float]:
        """基于关键词的初步分析"""
        text_lower = text.lower()
        
        scam_score = sum(1 for word in self.SCAM_KEYWORDS if word in text_lower)
        ad_score = sum(1 for word in self.AD_KEYWORDS if word in text_lower)
        normal_score = sum(1 for word in self.NORMAL_KEYWORDS if word in text_lower)
        
        total = scam_score + ad_score + normal_score
        if total == 0:
            return (0.33, 0.33, 0.34)
        
        return (
            normal_score / total,
            ad_score / total,
            scam_score / total
        )

    def pattern_analysis(self, text: str) -> Tuple[float, float, float]:
        """基于正则模式的测试邮件检测"""
        text_lower = text.lower()
        
        # 检测测试邮件特征
        test_score = 0
        for pattern in self.TEST_PATTERNS:
            if re.search(pattern, text_lower, re.IGNORECASE):
                test_score += 1
        
        # 如果包含测试特征，高度倾向于广告邮件
        if test_score > 0:
            return (0.05, 0.9, 0.05)
        
        return (0.33, 0.33, 0.34)

    def length_analysis(self, text: str) -> Tuple[float, float, float]:
        """基于文本长度的分析"""
        words = text.split()
        word_count = len(words)
        
        # 超短文本可能是测试或垃圾邮件
        if word_count <= 3:
            return (0.2, 0.5, 0.3)
        # 中等长度更可能是正常邮件
        elif 4 <= word_count <= 50:
            return (0.6, 0.25, 0.15)
        # 超长文本可能是广告或正式文档
        else:
            return (0.4, 0.4, 0.2)

    def call_llm_simple_classification(self, text: str) -> Tuple[float, float, float]:
        """使用LLM进行简单的三选一分类"""
        prompt = f"""请分析以下邮件内容，判断它最可能属于哪一类：
1. 正常邮件 - 日常工作交流、商务沟通、博客评论回复通知等
2. 广告邮件 - 商业推广、促销信息等
3. 诈骗邮件 - 欺诈、钓鱼、骚扰等恶意邮件

邮件内容："{text}"

请只输出一个符合上述邮件内容的数字：1（正常）、2（广告）或3（诈骗），不要输出其他任何内容。"""

        payload = {
            "model": OLLAMA_MODEL,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.1
            }
        }

        try:
            req = urllib_request.Request(
                OLLAMA_API_URL,
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"}
            )
            with urllib_request.urlopen(req, timeout=30) as response:
                result = json.loads(response.read().decode("utf-8"))
                response_text = result.get("response", "").strip()
                
                # 解析响应
                if "1" in response_text:
                    return (0.8, 0.1, 0.1)
                elif "2" in response_text:
                    return (0.1, 0.8, 0.1)
                elif "3" in response_text:
                    return (0.1, 0.1, 0.8)
                else:
                    logger.warning(f"LLM返回无法解析的响应: {response_text}")
                    return (0.33, 0.33, 0.34)
                    
        except Exception as e:
            logger.error(f"LLM调用失败: {str(e)}")
            return (0.33, 0.33, 0.34)

    def classify(self, text: str) -> Tuple[float, float, float]:
        """综合分类方法"""
        if not text.strip():
            return (0.34, 0.33, 0.33)
        
        # 各分析方法的结果
        keyword_scores = self.keyword_analysis(text)
        pattern_scores = self.pattern_analysis(text)
        length_scores = self.length_analysis(text)
        llm_scores = self.call_llm_simple_classification(text)
        
        # 加权平均
        final_normal = (
            keyword_scores[0] * self.rule_weights['keyword_match'] +
            pattern_scores[0] * self.rule_weights['pattern_match'] +
            length_scores[0] * self.rule_weights['length_analysis'] +
            llm_scores[0] * self.rule_weights['llm_analysis']
        )
        
        final_ad = (
            keyword_scores[1] * self.rule_weights['keyword_match'] +
            pattern_scores[1] * self.rule_weights['pattern_match'] +
            length_scores[1] * self.rule_weights['length_analysis'] +
            llm_scores[1] * self.rule_weights['llm_analysis']
        )
        
        final_scam = (
            keyword_scores[2] * self.rule_weights['keyword_match'] +
            pattern_scores[2] * self.rule_weights['pattern_match'] +
            length_scores[2] * self.rule_weights['length_analysis'] +
            llm_scores[2] * self.rule_weights['llm_analysis']
        )
        
        # 归一化
        total = final_normal + final_ad + final_scam
        if total > 0:
            return (
                final_normal / total,
                final_ad / total,
                final_scam / total
            )
        else:
            return (0.34, 0.33, 0.33)

# 初始化分类器
classifier = EmailClassifier()

@app.route('/health', methods=['GET'])
def health_check():
    """健康检查"""
    try:
        test_payload = {
            "model": OLLAMA_MODEL,
            "prompt": "test",
            "stream": False
        }
        req = urllib_request.Request(
            OLLAMA_API_URL,
            data=json.dumps(test_payload).encode("utf-8"),
            headers={"Content-Type": "application/json"}
        )
        with urllib_request.urlopen(req, timeout=5):
            return jsonify({'status': 'healthy', 'ollama': 'connected'})
    except Exception as e:
        logger.error(f"健康检查失败: {str(e)}")
        return jsonify({
            'status': 'unhealthy',
            'ollama': 'disconnected',
            'error': str(e)
        }), 503

@app.route('/v1/models/emotion_model:predict', methods=['POST'])
def predict_emotion():
    """邮件分类预测接口"""
    try:
        data = request.get_json()
        if not data or 'instances' not in data:
            return jsonify({'error': 'Invalid request format'}), 400
            
        instances = data.get('instances', [])
        if not instances:
            return jsonify({'predictions': []})

        predictions = []
        for instance in instances:
            # 提取文本内容
            token = instance.get('token', [])
            text = " ".join(token) if isinstance(token, list) else str(token)
            
            # 使用混合分类器
            normal_score, ad_score, scam_score = classifier.classify(text)
            predictions.append([normal_score, ad_score, scam_score])
            
            logger.info(f"分类结果: '{text[:30]}...' -> 正常:{normal_score:.3f}, 广告:{ad_score:.3f}, 诈骗:{scam_score:.3f}")
                
        return jsonify({'predictions': predictions})
        
    except Exception as e:
        logger.error(f"请求处理失败: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/classify', methods=['POST'])
def classify_direct():
    """直接分类接口，更简单的输入格式"""
    try:
        data = request.get_json()
        if not data or 'text' not in data:
            return jsonify({'error': 'Missing text field'}), 400
            
        text = data['text']
        normal_score, ad_score, scam_score = classifier.classify(text)
        
        return jsonify({
            'normal': normal_score,
            'ad': ad_score,
            'scam': scam_score,
            'prediction': max(['normal', 'ad', 'scam'], 
                            key=lambda x: [normal_score, ad_score, scam_score][['normal','ad','scam'].index(x)])
        })
        
    except Exception as e:
        logger.error(f"直接分类失败: {str(e)}")
        return jsonify({'error': 'Classification failed'}), 500

@app.route('/', methods=['GET'])
def index():
    """服务信息"""
    return jsonify({
        'service': 'Enhanced Email Classification Service',
        'version': '2.0.0',
        'approach': 'Hybrid (Rules + LLM)',
        'endpoints': {
            'health': '/health',
            'predict': '/v1/models/emotion_model:predict',
            'classify': '/classify'
        }
    })

if __name__ == "__main__":
    logger.info(f"启动增强版邮件分类服务，监听 {SERVER_HOST}:{SERVER_PORT}")
    logger.info(f"使用混合分类方法：规则 + LLM")
    logger.info(f"Ollama 模型: {OLLAMA_MODEL}")
    
    app.run(host=SERVER_HOST, port=SERVER_PORT, debug=False)

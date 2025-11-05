"""
问题相关API
"""
from flask import Blueprint, jsonify, request
from backend.models.problem_model import (
    get_all_problems, get_problem_by_id, add_problem,
    update_problem, delete_problem, update_problem_tags
)
from backend.collectors.service import CollectionService
import json
import os
import requests

problems_bp = Blueprint('problems', __name__, url_prefix='/api/problems')

# 初始化采集服务（使用组合模式）
# 检查是否使用第三方API聚合平台
use_third_party = os.getenv('USE_THIRD_PARTY_API', 'false').lower() == 'true'
collection_service = CollectionService(use_third_party=use_third_party)

@problems_bp.route('/list', methods=['GET'])
def list_problems():
    """获取问题列表"""
    category = request.args.get('category')
    tag = request.args.get('tag')
    
    problems = get_all_problems(category=category, tag=tag)
    return jsonify({'success': True, 'data': problems})

@problems_bp.route('/<int:problem_id>', methods=['GET'])
def get_problem(problem_id):
    """获取问题详情"""
    problem = get_problem_by_id(problem_id)
    if problem:
        return jsonify({'success': True, 'data': problem})
    return jsonify({'success': False, 'message': '问题不存在'}), 404

@problems_bp.route('/', methods=['POST'])
def create_problem():
    """创建问题"""
    data = request.get_json()
    
    if not data.get('title') or not data.get('content'):
        return jsonify({'success': False, 'message': '标题和内容不能为空'}), 400
    
    problem_id = add_problem(
        title=data.get('title'),
        content=data.get('content'),
        category=data.get('category'),
        tags=data.get('tags', []),
        related_book_ids=data.get('related_book_ids')
    )
    
    return jsonify({
        'success': True,
        'data': {'id': problem_id}
    }), 201

@problems_bp.route('/<int:problem_id>', methods=['PUT'])
def update_problem_api(problem_id):
    """更新问题"""
    data = request.get_json()
    
    result = update_problem(
        problem_id=problem_id,
        title=data.get('title'),
        content=data.get('content'),
        category=data.get('category'),
        tags=data.get('tags'),
        related_book_ids=data.get('related_book_ids')
    )
    
    if result:
        return jsonify({'success': True, 'message': '更新成功'})
    return jsonify({'success': False, 'message': '更新失败或问题不存在'}), 404

@problems_bp.route('/<int:problem_id>', methods=['DELETE'])
def delete_problem_api(problem_id):
    """删除问题"""
    result = delete_problem(problem_id)
    if result:
        return jsonify({'success': True, 'message': '删除成功'})
    return jsonify({'success': False, 'message': '删除失败或问题不存在'}), 404

@problems_bp.route('/<int:problem_id>/tags', methods=['PUT'])
def update_tags(problem_id):
    """更新问题标签"""
    data = request.get_json()
    tags = data.get('tags', [])
    
    result = update_problem_tags(problem_id, tags)
    if result:
        return jsonify({'success': True, 'message': '标签更新成功'})
    return jsonify({'success': False, 'message': '更新失败或问题不存在'}), 404

@problems_bp.route('/init-sample', methods=['POST'])
def init_sample_data():
    """初始化示例数据（股票市场常见问题）"""
    sample_problems = [
        {
            'title': '如何判断股票的买入时机？',
            'content': '买入时机的判断需要考虑多个因素：\n1. 技术面分析：看K线图、均线、MACD等指标\n2. 基本面分析：公司财务状况、行业前景、市场环境\n3. 市场情绪：关注市场热点和资金流向\n4. 风险管理：设置止损点，控制仓位',
            'category': '金融',
            'tags': ['兴趣', '待办']
        },
        {
            'title': '股票被套后应该怎么办？',
            'content': '股票被套的应对策略：\n1. 分析被套原因：是基本面变坏还是市场情绪影响\n2. 如果基本面良好：可以适当补仓摊低成本\n3. 如果基本面恶化：考虑止损出局\n4. 短期被套可以等待反弹，长期被套需要重新评估投资逻辑',
            'category': '金融',
            'tags': ['兴趣', '待办']
        },
        {
            'title': '如何选择成长股和价值股？',
            'content': '成长股和价值股的选择标准：\n\n成长股特征：\n- 营收和利润高速增长\n- 行业处于快速发展期\n- 具有核心竞争力\n\n价值股特征：\n- 估值相对较低（低PE、PB）\n- 稳定的盈利能力\n- 高分红率\n\n选择策略：\n- 成长股适合风险承受能力强的投资者\n- 价值股适合稳健型投资者',
            'category': '金融',
            'tags': ['兴趣']
        },
        {
            'title': '股票分红对股价的影响？',
            'content': '股票分红的影响：\n1. 除权除息：分红后股价会相应下调\n2. 填权行情：如果公司业绩持续增长，股价可能回到分红前水平\n3. 投资价值：高分红公司通常现金流充裕，适合稳健投资者\n4. 税务考虑：不同持股时间税率不同',
            'category': '金融',
            'tags': ['已完成']
        },
        {
            'title': '如何理解股票的技术指标？',
            'content': '常用技术指标解读：\n\n1. MA均线：\n   - 5日、10日短期均线\n   - 20日、60日中期均线\n   - 120日、250日长期均线\n   - 金叉死叉判断买卖点\n\n2. MACD：\n   - 快慢线交叉信号\n   - 柱状图强弱\n\n3. KDJ：\n   - 超买超卖指标\n   - 80以上超买，20以下超卖\n\n4. RSI：\n   - 相对强弱指标\n   - 结合其他指标使用',
            'category': '金融',
            'tags': ['兴趣', '待办']
        },
        {
            'title': '股票投资的风险控制方法？',
            'content': '风险控制策略：\n1. 仓位管理：不要满仓，保留一定现金\n2. 分散投资：不要把所有资金投入单一股票\n3. 止损止盈：设置明确的目标价位\n4. 分批建仓：避免一次性买入\n5. 关注市场情绪：避免在极端情绪下操作\n6. 定期复盘：总结投资经验教训',
            'category': '金融',
            'tags': ['兴趣']
        }
    ]
    
    added_count = 0
    for problem in sample_problems:
        try:
            add_problem(
                title=problem['title'],
                content=problem['content'],
                category=problem['category'],
                tags=problem['tags']
            )
            added_count += 1
        except Exception as e:
            print(f"添加示例问题失败：{problem['title']}, 错误：{str(e)}")
    
    return jsonify({
        'success': True,
        'message': f'成功创建 {added_count} 条示例问题',
        'data': {'added': added_count}
    })

@problems_bp.route('/<int:problem_id>/analyze', methods=['POST'])
def analyze_problem(problem_id):
    """使用AI分析问题并给出最优解"""
    problem = get_problem_by_id(problem_id)
    if not problem:
        return jsonify({'success': False, 'message': '问题不存在'}), 404
    
    try:
        # 构建分析提示
        prompt = f"""请分析以下股票市场相关问题，并提供详细的最优解决方案：

问题标题：{problem['title']}
问题内容：{problem['content']}

请从以下几个角度进行分析：
1. 问题的核心要点
2. 相关的投资策略和建议
3. 风险提示
4. 具体的操作建议

请提供结构清晰、专业实用的分析结果。"""
        
        # 使用免费的AI服务（这里使用Hugging Face Inference API的免费模型）
        # 如果没有配置API，可以使用简单的规则回复
        api_url = os.getenv('HUGGINGFACE_API_URL', '')
        api_key = os.getenv('HUGGINGFACE_API_KEY', '')
        
        if api_url and api_key:
            # 使用Hugging Face API
            headers = {
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json'
            }
            
            payload = {
                'inputs': prompt,
                'parameters': {
                    'max_new_tokens': 500,
                    'temperature': 0.7
                }
            }
            
            try:
                response = requests.post(api_url, json=payload, headers=headers, timeout=30)
                if response.status_code == 200:
                    result = response.json()
                    # 处理不同的响应格式
                    if isinstance(result, list) and len(result) > 0:
                        if 'generated_text' in result[0]:
                            analysis = result[0]['generated_text']
                        else:
                            analysis = json.dumps(result[0], ensure_ascii=False)
                    else:
                        analysis = json.dumps(result, ensure_ascii=False)
                else:
                    raise Exception(f"API请求失败: {response.status_code}")
            except Exception as e:
                print(f"AI分析API调用失败: {str(e)}")
                # 使用备用方案
                analysis = generate_fallback_analysis(problem)
        else:
            # 使用备用方案（基于规则的简单分析）
            analysis = generate_fallback_analysis(problem)
        
        return jsonify({
            'success': True,
            'data': {
                'problem_id': problem_id,
                'analysis': analysis
            }
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'分析失败: {str(e)}'
        }), 500

@problems_bp.route('/collect', methods=['POST'])
def collect_questions():
    """从社交平台采集问题"""
    data = request.get_json()
    topic = data.get('topic', '').strip()
    max_results = data.get('max_results', 50)
    platform = data.get('platform')  # 可选，指定平台
    auto_save = data.get('auto_save', False)  # 是否自动保存
    collect_answers = data.get('collect_answers', True)  # 是否采集回答
    max_answers_per_question = data.get('max_answers_per_question', 3)  # 每个问题最多采集的回答数
    min_answer_upvotes = data.get('min_answer_upvotes', 10)  # 回答最小点赞数要求
    
    if not topic:
        return jsonify({
            'success': False,
            'message': '主题不能为空'
        }), 400
    
    try:
        result = collection_service.collect_questions(
            topic=topic,
            max_results=max_results,
            platform=platform,
            auto_save=auto_save,
            collect_answers=collect_answers,
            max_answers_per_question=max_answers_per_question,
            min_answer_upvotes=min_answer_upvotes
        )
        return jsonify(result)
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'采集失败: {str(e)}'
        }), 500

@problems_bp.route('/collect/platforms', methods=['GET'])
def get_collect_platforms():
    """获取可用的采集平台列表"""
    try:
        platforms = collection_service.get_available_platforms()
        # 获取所有平台（包括不可用的），用于显示
        all_platforms = collection_service.get_all_platforms()
        return jsonify({
            'success': True,
            'data': {
                'available': platforms,
                'all': all_platforms
            }
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'获取平台列表失败: {str(e)}'
        }), 500

@problems_bp.route('/<int:problem_id>/answers', methods=['GET'])
def get_problem_answers(problem_id):
    """获取问题的回答列表"""
    try:
        import backend.models.answer_model as answer_model
        answers = answer_model.get_answers_by_problem_id(problem_id)
        return jsonify({
            'success': True,
            'data': answers
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'获取回答失败: {str(e)}'
        }), 500

@problems_bp.route('/collect/diagnose', methods=['GET'])
def diagnose_collection():
    """诊断采集系统"""
    try:
        from backend.collectors.diagnostics import diagnose_collectors, check_collection_flow
        from backend.collectors.interfaces import CollectionConfig
        
        # 基础诊断
        basic_diagnosis = diagnose_collectors()
        
        # 流程诊断
        test_config = CollectionConfig(
            topic='股票',
            max_results=5,
            collect_answers=True,
            max_answers_per_question=2,
            min_answer_upvotes=10
        )
        flow_diagnosis = check_collection_flow(test_config)
        
        return jsonify({
            'success': True,
            'data': {
                'collectors': basic_diagnosis,
                'flow': flow_diagnosis
            }
        })
    except Exception as e:
        import traceback
        return jsonify({
            'success': False,
            'message': f'诊断失败: {str(e)}',
            'traceback': traceback.format_exc()
        }), 500

@problems_bp.route('/collect/test-api', methods=['GET'])
def test_platform_apis():
    """测试平台API可用性"""
    try:
        from backend.collectors.api_test import test_all_platforms
        
        print("[API测试] 收到API可用性测试请求")
        results = test_all_platforms()
        
        return jsonify({
            'success': True,
            'data': results
        })
    except Exception as e:
        import traceback
        print(f"[API测试] 测试失败: {str(e)}")
        print(f"[API测试] 错误详情: {traceback.format_exc()}")
        return jsonify({
            'success': False,
            'message': f'API测试失败: {str(e)}',
            'traceback': traceback.format_exc()
        }), 500

def generate_fallback_analysis(problem):
    """生成备用分析（当AI服务不可用时）"""
    title = problem['title']
    content = problem['content']
    
    # 基于规则的简单分析
    analysis = f"""# AI分析：{title}

## 问题概述
{content}

## 分析要点

### 1. 核心问题识别
这是一个关于股票投资策略的问题。需要从多个维度进行分析和决策。

### 2. 关键考虑因素
- **市场环境**：当前市场处于什么阶段（牛市、熊市、震荡市）
- **个股基本面**：公司的财务状况、行业地位、成长性
- **技术面分析**：价格走势、成交量、技术指标
- **风险管理**：仓位控制、止损设置

### 3. 建议策略
- 建议结合基本面和技术面进行综合分析
- 制定明确的投资计划和风险控制措施
- 根据个人风险承受能力调整策略

### 4. 风险提示
- 股票投资存在风险，请根据自身情况谨慎决策
- 建议分散投资，不要过度集中
- 定期复盘，及时调整策略

---
*注：这是基于规则的初步分析。如需更专业的AI分析，请配置AI服务API。*"""
    
    return analysis


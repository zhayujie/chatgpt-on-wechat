import re

def contains_apology(text):
    if text is None:
        return []
    
    apology_phrases = [
        "很抱歉", "对不起", "抱歉", "无法提供", "不能提供", "不能浏览", "无法实时", "AI助手", 
        "不能查询", "无法查询", "作为AI", "作为人工智能", "作为一个基于", "历史数据", "历史训练",
        "作为一个AI", "作为一个文本交互", "无法直接", "上网搜索", "无法解析", "访问网页","人工智能模型",
        "不能直接", "直接访问", "网页链接"
    ]
    matched_phrases = []
    for phrase in apology_phrases:
        if phrase in text:
            position = text.index(phrase)
            # 如果文字不足100字，则按100字计算，目的是增加不足100字的文字的各项评分值
            score = 1 - (position / max(100, len(text)))
            score = round(score, 2)  # 将 score 四舍五入保留2位小数
            matched_phrases.append((phrase, score))
    return matched_phrases

def contains_alternative_suggestion(text):
    if text is None:
        return []

    suggestion_phrases = [
        "建议您", "查询", "查阅", "查看", "访问", "使用", "通过", "联系", "获取", "查找"
    ]
    matched_phrases = []
    for phrase in suggestion_phrases:
        if phrase in text:
            position = text.index(phrase)
            # 如果文字不足100字，则按100字计算，目的是增加不足100字的文字的各项评分值
            score = 1 - (position / max(100, len(text)))
            score = round(score, 2)  # 将 score 四舍五入保留2位小数
            matched_phrases.append((phrase, score))
    return matched_phrases

def contains_information_terms(text):
    if text is None:
        return []

    information_terms = [
        "信息", "数据", "消息", "动态", "最新预报", "天气", "气象", "最新的", "新闻", "财经新闻", "股票"
        "财务数据", "实时更新", "最新财务", "最新信息", "实时信息", "指数数据", "上证指数", "A股", "收盘"
    ]
    matched_terms = []
    for term in information_terms:
        if term in text:
            position = text.index(term)
            # 如果文字不足100字，则按100字计算，目的是增加不足100字的文字的各项评分值
            score = 1 - (position / max(100, len(text)))
            score = round(score, 2)  # 将 score 四舍五入保留2位小数
            matched_terms.append((term, score))
    return matched_terms



#长度倾向值=(120-总字数)/60 越大越像是"很抱歉，无法获取"，越小越不像
def calculate_length_tendency(text):
    char_count = len(text) if text is not None else 0
    length_tendency = (120 - char_count) / 60
    length_tendency = round(length_tendency, 2)   # 四舍五入保留2位小数
    return length_tendency



# 根据AI回复的文本 判断决定需不需要实时搜索
def analyze_text_features__need_search(text):
    
    if text is not None and "我要上网查询后才能回答" in text and text.index("我要上网查询后才能回答") <= 99 :
        return "LLM已明确表示：【我要上网查询后才能回答】", 99999

    matched_apologies = contains_apology(text)
    matched_suggestions = contains_alternative_suggestion(text)
    matched_info_terms = contains_information_terms(text)
    
    matched_count = (len(matched_apologies) > 0) + (len(matched_suggestions) > 0) + (len(matched_info_terms) > 0)
    matched_features = {
        "抱歉类": matched_apologies,
        "建议类": matched_suggestions,
        "信息类": matched_info_terms
    }
    
    # 计算每一类的总评分值，并保留2位小数
    apologies_score_sum = round(sum(score for _, score in matched_apologies), 2)
    suggestions_score_sum = round(sum(score for _, score in matched_suggestions), 2)
    info_terms_score_sum = round(sum(score for _, score in matched_info_terms), 2)

    # 计算每一类的平均评分值，并保留2位小数
    apologies_avg_score = round(apologies_score_sum / max(1, len(matched_apologies)), 2)
    suggestions_avg_score = round(suggestions_score_sum / max(1, len(matched_suggestions)), 2)
    info_terms_avg_score = round(info_terms_score_sum / max(1, len(matched_info_terms)), 2)

    # 返回每一类的总评分值以及总的评分值
    sum_of_scores = apologies_score_sum + suggestions_score_sum + info_terms_score_sum
    sum_of_scores = round(sum_of_scores, 2)  # 将 score 四舍五入保留2位小数
    
    

    #增加计算 “修正后总分” 功能：目的是考虑 3 类词语的先后次序关系，作为判断依据之一
    #
    #如果 抱歉类平均分 > 建议类平均分 
    #则 修正后总分= 总分:{sum_of_scores} + 0.3
    #否则 修正后总分= 总分:{sum_of_scores} - 0.3
    #
    #如果 抱歉类平均分 > 信息类平均分 
    #则 修正后总分= 修正后总分 + 0.3
    #否则 修正后总分= 修正后总分 - 0.3
    # 
    adjusted_score = sum_of_scores
    if apologies_avg_score > suggestions_avg_score:
        adjusted_score += 0.3
    else:
        adjusted_score -= 0.3
    #
    if apologies_avg_score > info_terms_avg_score:
        adjusted_score += 0.3
    else:
        adjusted_score -= 0.3
    #
    adjusted_score = round(adjusted_score, 2)
    #
    #修正后总分 = 修正后总分 + 长度倾向值      长度倾向值 = (120-总字数)/60 越大越像是"很抱歉，无法获取"，越小越不像
    length_tendency = calculate_length_tendency(text)
    final_score = round(adjusted_score + length_tendency, 2)

    

    #把分析结果用美观的格式组成字符串，方便调用者直接显示查看结果
    analyze_result_string = (
        text[:60] + "\n" +
        f"词语:{matched_count} 明细:{matched_features}\n" +
        f"三小类合计分: 抱歉类 {apologies_score_sum}, 建议类 {suggestions_score_sum}, 信息类 {info_terms_score_sum}\n" +
        f"三小类平均分: 抱歉类 {apologies_avg_score}, 建议类 {suggestions_avg_score}, 信息类 {info_terms_avg_score}\n" +
        f"原总分:{sum_of_scores}  按3类词先后次序修正后总分:{adjusted_score}  再依长度倾向值{length_tendency}修正后最终总分:{final_score}\n" +
        "--------------"
    ) if text is not None else "收到的回复文本为空 None ，无需分析\n--------------------------------"

    return analyze_result_string, final_score

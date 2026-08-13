# Editor Report

## 总体判断
- 内容分：__/100
- 交付状态：阻塞 / 内容修订 / 可交下游编辑
- 一句话诊断：

## P0 阻塞问题

## P1 严重问题

## P2 一般问题

## P3 表达问题（交给去 AI 味 Skill）

## 分项评分
| 维度 | 得分 | 满分 | 证据 |
|---|---:|---:|---|
| 核心观点强度 |  | 15 |  |
| 独特性与信息增量 |  | 15 |  |
| 论证与证据 |  | 15 |  |
| 结构与推进 |  | 15 |  |
| 具体性 |  | 10 |  |
| 读者价值 |  | 10 |  |
| 作者经验与判断 |  | 10 |  |
| 文风一致性 |  | 5 |  |
| 完成度 |  | 5 |  |

## 补充检查项

### 结构审查
- [ ] 文章兑现所选原型的核心承诺
- [ ] 示例无重复展开（第二次应折叠为回调）
- [ ] 开发者视角段落已检查（不影响理解时删除）

### 逻辑审查
- [ ] claim→mechanism 2-3 段内
- [ ] A vs B 已结构化对比
- [ ] "So what" 测试通过
- [ ] 无自相矛盾

### 事实核查
- [ ] 数字准确且有来源
- [ ] 引用存在且未曲解
- [ ] 日期和名称正确
- [ ] 比较公平（apples-to-apples）
- [ ] 学科分类准确

### 视角审计
- [ ] 开发者/产品/用户三视角分离

## 修订计划
1. 
2. 
3. 

## 交接保护项
- 不得改变的事实：
- 不得改变的立场：
- 必须保留的原话：
- 待作者确认：

---

## JSON 输出模板（可选，用于校准和程序化处理）

```json
{
  "version": 1,
  "article_id": "",
  "reviewer": "",
  "timestamp": "",
  "overall_score": 0,
  "delivery_status": "blocked | revise | handoff",
  "diagnosis": "",
  "scores": {
    "core_strength": {"score": 0, "max": 15, "evidence": ""},
    "uniqueness": {"score": 0, "max": 15, "evidence": ""},
    "argument_evidence": {"score": 0, "max": 15, "evidence": ""},
    "structure": {"score": 0, "max": 15, "evidence": ""},
    "specificity": {"score": 0, "max": 10, "evidence": ""},
    "reader_value": {"score": 0, "max": 10, "evidence": ""},
    "author_judgment": {"score": 0, "max": 10, "evidence": ""},
    "voice_consistency": {"score": 0, "max": 5, "evidence": ""},
    "completeness": {"score": 0, "max": 5, "evidence": ""}
  },
  "issues": {
    "p0": [],
    "p1": [],
    "p2": [],
    "p3": []
  },
  "checklist": {
    "structural": {"passed": false, "notes": ""},
    "logic": {"passed": false, "notes": ""},
    "fact_check": {"passed": false, "notes": ""},
    "perspective": {"passed": false, "notes": ""}
  },
  "strengths": [],
  "improvements": [],
  "handoff": {
    "preserve_facts": [],
    "preserve_stance": [],
    "preserve_quotes": [],
    "author_confirmations": []
  }
}
```

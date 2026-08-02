---
name: coc-dice
description: "处理 CoC 7 版掷骰、检定、奖励/惩罚、对抗、伤害和理智损失。"
---
# CoC7掷骰
脚本 `scripts/coc7_dice.py` 仅用标准库和 `secrets`，每次输出一条 JSON，不写固定日志：
`python scripts/coc7_dice.py roll 1d6+2`
`python scripts/coc7_dice.py check --skill 60 --difficulty hard --bonus 1`
`python scripts/coc7_dice.py opposed --skill-a 55 --skill-b 40`
`python scripts/coc7_dice.py damage 1d10+2 --armor 3`
`python scripts/coc7_dice.py san --san 45 --loss 0/1d6`
投掷前确定目的、技能/属性、公式、目标、修正、明/暗骰和后果；参数确定后不得为剧情改动。规则：d100≤最终值成功；困难/极难=floor(值/2)/floor(值/5)；01通常大成功；技能<50时96-00通常大失败，技能≥50通常仅00。奖励/惩罚骰改十位骰，不作百分比加减；对抗按大成功>极难>困难>普通>失败>大失败；伤害扣护甲；SAN按当前值及场景损失处理。明骰公开结果，暗骰只给必要叙事。定位到用户指定日志才追加完整 JSON；找不到则说明未写入。幸运、改骰、重骰须先确认。

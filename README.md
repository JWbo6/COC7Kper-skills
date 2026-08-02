# COC7Kper Skills

一组面向中文 CoC 7 版跑团的 Codex/ZCode Skills。它们用于工作区初始化、建团、车卡、主持、掷骰、记录和结团归档。

> 本项目是社区维护的非官方工具集，与 Chaosium 无隶属、赞助或授权关系。`coc-shared/references/coc7-checks.md` 只是规则辅助摘要，不替代正版规则书；规则冲突时以你拥有的正式规则书、模组和已确认房规为准。

## 快速安装

### Linux / macOS

直接安装全部 Skill：

```bash
curl -fsSL https://raw.githubusercontent.com/JWbo6/COC7Kper-skills/main/install.sh | bash
```

审阅后再安装：

```bash
curl -fsSL https://raw.githubusercontent.com/JWbo6/COC7Kper-skills/main/install.sh -o /tmp/coc7kper-install.sh
less /tmp/coc7kper-install.sh
bash /tmp/coc7kper-install.sh
```

只安装指定 Skill：

```bash
curl -fsSL https://raw.githubusercontent.com/JWbo6/COC7Kper-skills/main/install.sh -o /tmp/coc7kper-install.sh
less /tmp/coc7kper-install.sh
bash /tmp/coc7kper-install.sh coc-dice coc-kp
```

自定义安装目录或覆盖已有版本：

```bash
bash /tmp/coc7kper-install.sh --destination "$HOME/.codex/skills" --force
```

### Windows PowerShell

审阅脚本后执行：

```powershell
Invoke-WebRequest `
  -Uri "https://raw.githubusercontent.com/JWbo6/COC7Kper-skills/main/install.ps1" `
  -OutFile "$env:TEMP\coc7kper-install.ps1"
Get-Content "$env:TEMP\coc7kper-install.ps1"
& "$env:TEMP\coc7kper-install.ps1"
```

只安装指定 Skill：

```powershell
Invoke-WebRequest `
  -Uri "https://raw.githubusercontent.com/JWbo6/COC7Kper-skills/main/install.ps1" `
  -OutFile "$env:TEMP\coc7kper-install.ps1"
& "$env:TEMP\coc7kper-install.ps1" -Skills coc-dice,coc-kp
```

自定义安装目录或覆盖已有版本：

```powershell
& "$env:TEMP\coc7kper-install.ps1" -Destination "$HOME\.codex\skills" -Force
```

安装器默认使用 `${CODEX_HOME}/skills`；未设置 `CODEX_HOME` 时，Linux/macOS 使用 `~/.codex/skills`，Windows PowerShell 使用 `$HOME\.codex\skills`。安装器只复制仓库中的 Skill，不上传或读取你的跑团资料。

## 包含的 Skill

| Skill | 适用请求 | 示例 |
| --- | --- | --- |
| `coc-campaign-manager` | CoC 跑团总入口和动作路由 | “帮我初始化这个 CoC 工作区”“继续上一场” |
| `coc-init-workspace` | 扫描或按明确要求初始化工作区 | “检查 `D:/COC` 的目录”“创建标准目录” |
| `coc-campaign` | 导入模组、创建独立团目录 | “用这个 PDF 建团”“读取这个 DOCX 模组” |
| `coc-character` | 创建、读取、修改和管理调查员角色卡 | “给我做一张 1920 年代调查员卡” |
| `coc-kp` | 主持剧情、调查、NPC、战斗和理智 | “继续调查”“处理这次战斗” |
| `coc-dice` | CoC 7 版检定、对抗、伤害和 SAN | “侦查 60 做困难检定，+1 奖励骰” |
| `coc-log` | 写入场次、线索、NPC、状态和恢复 | “记录刚才场景”“从上一场恢复” |
| `coc-archive` | 结团、冻结、整理最终角色卡和归档 | “结束这个团并归档记录” |

可以让总入口自动路由，也可以显式指定目录名，例如 `/coc-dice`。用户明确点名的 Skill 优先；一次只执行一个主写入流程。

## 初始化工作区

推荐先准备一个专用目录，然后让总入口或初始化 Skill 检查它：

```text
请把 C:/Games/COC 作为工作区根目录，只做只读扫描，报告现有目录和文件，不要创建或覆盖任何内容。
```

只有明确要求创建时，才执行初始化：

```text
请在 C:/Games/COC 初始化标准 CoC 工作区；已有文件不移动、不删除、不覆盖。
```

也可以直接使用随包脚本。脚本入口会创建传入的根目录，因此只读检查时不要把它当作纯查询工具：

```bash
python skills/coc-shared/scripts/coc_workspace.py init --root C:/Games/COC --dry-run
python skills/coc-shared/scripts/coc_workspace.py init --root C:/Games/COC
```

标准工作区大致如下：

```text
COC/
├─ COC须知/
│  ├─ 规则/
│  ├─ 车卡资料/
│  ├─ KP资料/
│  └─ 时代与设定/
├─ 模组/
│  ├─ 待整理/
│  ├─ 可开团/
│  └─ 已使用/
├─ 进行中的团/
│  └─ 年份-团名/
│     ├─ 00-团务/
│     ├─ 01-模组资料/
│     │  ├─ 原始模组/
│     │  └─ 主持人资料/
│     ├─ 02-调查员/
│     ├─ 03-场次记录/
│     ├─ 04-调查状态/
│     └─ 05-素材/
└─ 结束的团/
   └─ 年份-团名/
```

初始化默认是检查，不会自动读取固定规则书或历史团档。已有资料遇到同名、非空、只读、路径越界或版本冲突时，应停止对应写入并报告。

## 常用工作流

### 建团和导入模组

```text
请用 C:/资料/模组.pdf 创建“雾港来信”团，CoC 7 版，1920 年代；先报告缺失信息和源文件哈希。
```

外部模组源保持原位只读。新建团时必须把副本放入 `01-模组资料/原始模组/`，并在模组索引中记录外部绝对路径、团内相对路径、大小、mtime、SHA-256、解析状态和 `copy_status`。副本哈希不一致或目标冲突时停止。

脚本示例：

```bash
python skills/coc-shared/scripts/coc_workspace.py create-campaign \
  --root C:/Games/COC --name 雾港来信 --source C:/资料/模组.pdf --dry-run
```

### 车卡、主持和记录

```text
请在 C:/Games/COC/进行中的团/2026-雾港来信 下为玩家小林创建一名调查员，缺失信息先问我。
请继续上一场，只读取这个团的当前状态和最后有效场次记录。
请把刚才的线索、NPC 和角色变化写入指定团目录，并保留 event_id 和 revision。
```

JSON/JSONL 保存结构化事实和追加事件，Markdown 保存叙事、摘要和回顾。稳定 ID 用于关联，名称只用于显示；更新快照前读取并核对 `revision`，日志只追加，写后重新读取校验。

### 命令行掷骰

`coc-dice` 自带标准库脚本，每次输出一条 JSON，不会自动写固定日志：

```bash
python skills/coc-dice/scripts/coc7_dice.py roll 1d6+2
python skills/coc-dice/scripts/coc7_dice.py check --skill 60 --difficulty hard --bonus 1
python skills/coc-dice/scripts/coc7_dice.py opposed --skill-a 55 --skill-b 40
python skills/coc-dice/scripts/coc7_dice.py damage 1d10+2 --armor 3
python skills/coc-dice/scripts/coc7_dice.py san --san 45 --loss 0/1d6
```

投骰前先确定目的、公式、目标、修正、明/暗骰和后果。奖励/惩罚骰改变十位骰，不是百分比加减；幸运、改骰和重骰需要先取得明确确认。

### 结团归档

```text
请先对 C:/Games/COC/进行中的团/2026-雾港来信 做 dry-run，列出归档目标、文件哈希、缺失项和冲突；不要移动任何文件。
```

dry-run 检查通过并得到明确确认后，才复制或移动到归档目录。归档后默认只读，不覆盖已有目标，原始模组保持不变。

## 信息隔离

- `01-模组资料/主持人资料/` 和内部状态：KP 秘密。
- `00-团务/玩家可知信息.md`：只放已经公开的事实和玩家已知结果。
- 角色私密背景：只给对应玩家/角色和 KP。
- 原始模组：记录路径和解析状态，不把幕后段落复制到玩家文件。

如果用户要求查看幕后真相，应说明这是主持人秘密；可以提供不剧透的玩家视角总结。当前状态文件如果混合恢复信息和 KP 内部状态，也必须按 KP-only 处理。

## 参考资料和模板

`skills/coc-shared/references/` 下的 4 个文件全部是 UTF-8 Markdown 文字文件：

- `coc7-checks.md`：CoC 7 版判定、奖励/惩罚骰、对抗、战斗、SAN 和审计字段的非官方辅助摘要。
- `data-contract.md`：JSON/JSONL、稳定 ID、时间、revision、事件和 visibility 约定。
- `input-handling.md`：PDF、DOCX、XLSX、模组源文件和副本校验边界。
- `workflow-and-privacy.md`：路由、团状态机、KP/玩家隔离和写入冲突处理。

这些 references 是本项目围绕工作流和数据格式整理的文字规范；发布前检查确认它们不是二进制文件、没有仓库内重复副本，也没有作者/转载标记。不能据此宣称所有规则事实或通用概念均为原创。

`skills/coc-shared/assets/templates/` 包含工作区、团信息、场次、角色、线索、NPC、地点、道具和归档模板。模板是资源，不是用户当前团的数据。

## 安全和隐私

不要把当前团目录、玩家角色卡、模组原文、绝对本机路径、API 密钥或其他私人资料提交到这个仓库。安装器只复制 `skills/` 目录下的发布内容。使用公开仓库时，任何上传内容都可能被缓存或索引。

## 许可和归属

本项目的 Skill、脚本、模板和工作流文档由仓库维护者发布。CoC、Call of Cthulhu 及相关商标和版权归其各自权利人所有；本项目不代表官方。发布前请根据你的用途补充合适的开源许可证和第三方内容说明。

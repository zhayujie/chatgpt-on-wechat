<p align="center"><img src="https://github.com/user-attachments/assets/eca9a9ec-8534-4615-9e0f-96c5ac1d10a3" alt="CowAgent" width="550" /></p>

<p align="center">
  <a href="https://github.com/zhayujie/chatgpt-on-wechat/releases/latest"><img src="https://img.shields.io/github/v/release/zhayujie/chatgpt-on-wechat" alt="Latest release"></a>
  <a href="https://github.com/zhayujie/chatgpt-on-wechat/blob/master/LICENSE"><img src="https://img.shields.io/github/license/zhayujie/chatgpt-on-wechat" alt="License: MIT"></a>
  <a href="https://github.com/zhayujie/chatgpt-on-wechat"><img src="https://img.shields.io/github/stars/zhayujie/chatgpt-on-wechat?style=flat-square" alt="Stars"></a> <br/>
  [<a href="https://github.com/zhayujie/chatgpt-on-wechat/blob/master/README.md">中文</a>] | [<a href="https://github.com/zhayujie/chatgpt-on-wechat/blob/master/docs/en/README.md">English</a>] | [日本語]
</p>

**CowAgent** はLLMを搭載したAIスーパーアシスタントです。自律的なタスク計画、コンピュータや外部リソースの操作、Skillの作成・実行、長期記憶による継続的な成長が可能です。柔軟なモデル切り替えに対応し、テキスト・音声・画像・ファイルを処理でき、Web、Feishu（飛書）、DingTalk（釘釘）、WeCom Bot（企業微信ボット）、WeComアプリ、WeChat公式アカウントに統合可能で、個人のPCやサーバー上で24時間365日稼働できます。

<p align="center">
  <a href="https://cowagent.ai/">🌐 ウェブサイト</a> &nbsp;·&nbsp;
  <a href="https://docs.cowagent.ai/en/intro/index">📖 ドキュメント</a> &nbsp;·&nbsp;
  <a href="https://docs.cowagent.ai/en/guide/quick-start">🚀 クイックスタート</a> &nbsp;·&nbsp;
  <a href="https://link-ai.tech/cowagent/create">☁️ オンラインで試す</a>
</p>

## はじめに

> CowAgentは、すぐに使えるAIスーパーアシスタントであると同時に、高い拡張性を持つAgentフレームワークでもあります。新しいモデルインターフェース、チャネル、組み込みツール、Skillシステムを拡張することで、さまざまなカスタマイズニーズに柔軟に対応できます。

- ✅ **自律的タスク計画**: 複雑なタスクを理解し、自律的に実行計画を立て、目標達成までツールを呼び出しながら継続的に思考します。ツールを通じてファイル、ターミナル、ブラウザ、スケジューラなどのシステムリソースにアクセスできます。
- ✅ **長期記憶**: 会話の記憶をローカルファイルやデータベースに自動的に永続化します。コアメモリとデイリーメモリを含み、キーワード検索やベクトル検索に対応しています。
- ✅ **Skillシステム**: Skillの作成・実行エンジンを実装しており、複数の組み込みSkillを備え、自然言語での会話を通じたカスタムSkillの開発もサポートしています。
- ✅ **マルチモーダルメッセージ**: テキスト、画像、音声、ファイルなど、さまざまなメッセージタイプの解析・処理・生成・送信に対応しています。
- ✅ **複数モデル対応**: OpenAI、Claude、Gemini、DeepSeek、MiniMax、GLM、Qwen、Kimi、Doubaoなど、主要なモデルプロバイダーに対応しています。
- ✅ **マルチプラットフォームデプロイ**: ローカルPCやサーバー上で実行でき、Web、Feishu、DingTalk、WeChat公式アカウント、WeComアプリケーションに統合可能です。
- ✅ **ナレッジベース**: [LinkAI](https://link-ai.tech) プラットフォームを通じて、企業向けナレッジベース機能を統合できます。

## 免責事項

1. 本プロジェクトは [MIT License](/LICENSE) に基づいており、技術研究・学習を目的としています。利用者は現地の法律、規制、ポリシー、企業の社則を遵守する必要があります。違法行為や権利侵害となる利用は禁止されています。
2. Agentモードは通常のチャットモードよりも多くのトークンを消費します。効果とコストに基づいてモデルを選択してください。AgentはホストOSにアクセスできるため、信頼できる環境にデプロイしてください。
3. CowAgentはオープンソース開発に注力しており、いかなる暗号通貨の発行・参加・承認も行っていません。

## デモ

オンラインで試す（デプロイ不要）: [CowAgent](https://link-ai.tech/cowagent/create)

## 更新履歴

> **2026.02.27:** [v2.0.2](https://github.com/zhayujie/chatgpt-on-wechat/releases/tag/2.0.2) — Webコンソールの全面刷新（ストリーミングチャット、モデル/Skill/メモリ/チャネル/スケジューラ/ログ管理）、マルチチャネル同時実行、セッション永続化、Gemini 3.1 Pro / Claude 4.6 Sonnet / Qwen3.5 Plusなど新モデル追加。

> **2026.02.13:** [v2.0.1](https://github.com/zhayujie/chatgpt-on-wechat/releases/tag/2.0.1) — 組み込みWeb検索ツール、スマートコンテキストトリミング、ランタイム情報の動的更新、Windows互換性、スケジューラのメモリ喪失やFeishu接続問題などの修正。

> **2026.02.03:** [v2.0.0](https://github.com/zhayujie/chatgpt-on-wechat/releases/tag/2.0.0) — マルチステップタスク計画、長期記憶、組み込みツール、Skillフレームワーク、新モデル、チャネル最適化を備えたAIスーパーアシスタントへの全面アップグレード。

> **2025.05.23:** [v1.7.6](https://github.com/zhayujie/chatgpt-on-wechat/releases/tag/1.7.6) — Webチャネル最適化、AgentMeshマルチエージェントプラグイン、Baidu TTS、claude-4-sonnet/opus対応。

> **2025.04.11:** [v1.7.5](https://github.com/zhayujie/chatgpt-on-wechat/releases/tag/1.7.5) — wechatferryプロトコル、DeepSeekモデル、Tencent Cloud音声、ModelScope・Gitee-AI対応。

> **2024.12.13:** [v1.7.4](https://github.com/zhayujie/chatgpt-on-wechat/releases/tag/1.7.4) — Gemini 2.0モデル、Webチャネル、メモリリーク修正。

全更新履歴: [リリースノート](https://docs.cowagent.ai/en/releases/overview)

<br/>

## 🚀 クイックスタート

本プロジェクトは、インストール・設定・起動・管理をワンクリックで行えるスクリプトを提供しています：

```bash
bash <(curl -fsSL https://cdn.link-ai.tech/code/cow/run.sh)
```

実行後、デフォルトでWebサービスが起動します。`http://localhost:9899/chat` にアクセスしてチャットを開始できます。

スクリプトの使い方: [ワンクリックインストール](https://docs.cowagent.ai/en/guide/quick-start)

### 手動インストール

**1. プロジェクトのクローン**

```bash
git clone https://github.com/zhayujie/chatgpt-on-wechat
cd chatgpt-on-wechat/
```

**2. 依存関係のインストール**

```bash
pip3 install -r requirements.txt
pip3 install -r requirements-optional.txt   # 任意ですが推奨
```

**3. 設定**

```bash
cp config-template.json config.json
```

`config.json` にモデルのAPIキーとチャネルタイプを記入してください。詳細は[設定ドキュメント](https://docs.cowagent.ai/en/guide/manual-install)を参照してください。

**4. 実行**

```bash
python3 app.py
```

サーバーでバックグラウンド実行する場合：

```bash
nohup python3 app.py & tail -f nohup.out
```

### Dockerデプロイ

```bash
curl -O https://cdn.link-ai.tech/code/cow/docker-compose.yml
# docker-compose.yml を編集して設定を記入
sudo docker compose up -d
sudo docker logs -f chatgpt-on-wechat
```

<br/>

## モデル

主要なモデルプロバイダーに対応しています。Agentモードの推奨モデル：

| プロバイダー | 推奨モデル |
| --- | --- |
| MiniMax | `MiniMax-M2.7` |
| GLM | `glm-5-turbo` |
| Kimi | `kimi-k2.5` |
| Doubao | `doubao-seed-2-0-code-preview-260215` |
| Qwen | `qwen3.5-plus` |
| Claude | `claude-sonnet-4-6` |
| Gemini | `gemini-3.1-pro-preview` |
| OpenAI | `gpt-5.4` |
| DeepSeek | `deepseek-chat` |

各モデルの詳細設定については、[モデルドキュメント](https://docs.cowagent.ai/en/models/index)を参照してください。

### Coding Plan

Coding Planは各プロバイダーが提供する月額サブスクリプションパッケージで、高頻度のAgent利用に最適です。すべてのプロバイダーはOpenAI互換モードでアクセスできます：

```json
{
  "bot_type": "openai",
  "model": "MODEL_NAME",
  "open_ai_api_base": "PROVIDER_CODING_PLAN_API_BASE",
  "open_ai_api_key": "YOUR_API_KEY"
}
```

- `bot_type`: `openai` を指定
- `model`: プロバイダーがサポートするモデル名
- `open_ai_api_base`: プロバイダーのCoding Plan API Base（標準の従量課金とは異なります）
- `open_ai_api_key`: プロバイダーのCoding Plan APIキー

> 注意：Coding PlanのAPI BaseとAPIキーは、通常の従量課金のものとは別です。各プロバイダーのプラットフォームから取得してください。

対応プロバイダーには、Alibaba Cloud、MiniMax、Zhipu GLM、Kimi、Volcengineなどがあります。各プロバイダーの詳細設定については、[Coding Planドキュメント](https://docs.cowagent.ai/en/models/coding-plan)を参照してください。

<br/>

## チャネル

複数のプラットフォームに対応しています。`config.json` の `channel_type` を設定して切り替えます：

| チャネル | `channel_type` | ドキュメント |
| --- | --- | --- |
| Web（デフォルト） | `web` | [Webチャネル](https://docs.cowagent.ai/en/channels/web) |
| Feishu（飛書） | `feishu` | [Feishu設定](https://docs.cowagent.ai/en/channels/feishu) |
| DingTalk（釘釘） | `dingtalk` | [DingTalk設定](https://docs.cowagent.ai/en/channels/dingtalk) |
| WeCom Bot | `wecom_bot` | [WeCom Bot設定](https://docs.cowagent.ai/en/channels/wecom-bot) |
| WeComアプリ | `wechatcom_app` | [WeCom設定](https://docs.cowagent.ai/en/channels/wecom) |
| WeChat公式アカウント | `wechatmp` / `wechatmp_service` | [WeChat公式アカウント設定](https://docs.cowagent.ai/en/channels/wechatmp) |
| ターミナル | `terminal` | — |

複数チャネルを同時に有効化できます。カンマ区切りで指定してください：`"channel_type": "feishu,dingtalk"`

<br/>

## エンタープライズサービス

<a href="https://link-ai.tech" target="_blank"><img width="720" src="https://cdn.link-ai.tech/image/link-ai-intro.jpg"></a>

> [LinkAI](https://link-ai.tech/) は、企業や開発者向けのワンストップAIエージェントプラットフォームです。マルチモーダルLLM、ナレッジベース、Agentプラグイン、ワークフローを統合しています。主要プラットフォームへのワンクリック統合、SaaSおよびプライベートデプロイに対応しています。

<br/>

## 🔗 関連プロジェクト

- [bot-on-anything](https://github.com/zhayujie/bot-on-anything): 軽量で高い拡張性を持つLLMアプリケーションフレームワーク。Slack、Telegram、Discord、Gmailなどに対応。
- [AgentMesh](https://github.com/MinimalFuture/AgentMesh): エージェントチームの協調による複雑な問題解決のためのオープンソースのマルチエージェントフレームワーク。

## 🔎 よくある質問

FAQ: <https://github.com/zhayujie/chatgpt-on-wechat/wiki/FAQs>

## 🛠️ コントリビューション

新しいチャネルの追加を歓迎します。[Feishuチャネル](https://github.com/zhayujie/chatgpt-on-wechat/blob/master/channel/feishu/feishu_channel.py)を参考にしてください。また、新しいSkillのコントリビューションも歓迎します。[Skill Creatorドキュメント](https://github.com/zhayujie/chatgpt-on-wechat/blob/master/skills/skill-creator/SKILL.md)を参照してください。

## ✉ お問い合わせ

PRやIssueの提出を歓迎します。🌟 Starでプロジェクトをサポートしてください。ご質問がある場合は、[FAQリスト](https://github.com/zhayujie/chatgpt-on-wechat/wiki/FAQs)を確認するか、[Issues](https://github.com/zhayujie/chatgpt-on-wechat/issues)を検索してください。

## 🌟 コントリビューター

![cow contributors](https://contrib.rocks/image?repo=zhayujie/chatgpt-on-wechat&max=1000)

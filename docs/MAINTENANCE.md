# プロフィールの更新方法

## デザイン

ペンギン開発室の配色は、濃い紫 `#17142d`、ラベンダー `#c9bdff`、くすんだ紫 `#8f7bd1`、クリーム色 `#f6efdc`、くちばしの金色 `#e8cf77` です。ピクセルの装飾と金色の差し色を、プロフィールのアバターに合わせています。バナー、プロジェクトカード、フッターの背景は `#272537`、四角いドットは `#c0b7d3` です。READMEの各セクションは、背景が透けるドットの区切り線で分けています。

バナー、カード、フッター、街、活動の概要とヒートマップはオリジナルのSVGです。セクション構成は [uzuchan](https://github.com/uzuchan) さんのプロフィールを参考にしています。技術アイコンは [Skill Icons](https://github.com/tandpfun/skill-icons) を使用しています。

## 編集するファイル

- 自己紹介とプロジェクトの説明は `README.md`
- バナーは `assets/header.svg`
- プロジェクトカードは `assets/project-*.svg`
- 区切り線は `assets/pixel-divider.svg`
- 活動の概要、街、ヒートマップは `scripts/update_profile.py`

自己紹介と技術一覧は、Re:Decide、devlab-board、mcp-pr-review の公開READMEをもとに、使っている技術や試している構成を紹介しています。

## 自動更新

GitHub Actionsは毎日06:23（日本時間）に動きます。実行時刻はGitHubの都合で遅れることがあります。すぐに更新したいときは、Actions → Refresh profile visuals → Run workflow を選びます。ワークフローはリポジトリの一時的な `GITHUB_TOKEN` を使います。

公開リポジトリはREST APIで、過去1年分の日別コントリビューション数はGraphQLで取得します。非公開リポジトリの名前、説明、Issue、ソースコードは取得・公開しません。コントリビューション数はGitHubの集計ルールに従います。

リポジトリ数・スター数・主要言語の集計では、フォークとプロフィール用リポジトリを除きます。「リポジトリの主要言語」は、GitHubが各公開リポジトリに割り当てた言語です。mcp-pr-review の Blade 表示は、同梱の Laravel サンプルアプリに由来します。

活動があった日の建物の高さは `9 + 12 * log2(コントリビューション数 + 1)` で計算します。活動のなかった日は低いタイルで表します。ヒートマップの走査線は装飾です。

APIからデータを取得できない場合は、それまでの画像を保持します。活動カードはこのリポジトリ内のSVGを使っています。表示環境が `prefers-reduced-motion` に対応している場合、アニメーションは非表示になります。

## ローカルでの確認

Python 3.11以降と、ログイン済みのGitHub CLI（`gh`）を使います。

```sh
python3 -m unittest discover -s tests -v
python3 scripts/update_profile.py
```

自動生成するSVGは `assets/purple/` にあります。READMEの静的画像のURLはキャッシュ対策でコミットを固定しています。バナー、フッター、カード、区切り線の編集後は、READMEのURLのコミットを更新します。自動生成するSVGのURLは `main` を参照します。

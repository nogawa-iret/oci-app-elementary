# OCI Training Public Site

OCI 初級研修課題で利用するサンプル Web アプリケーションです。一般利用者向けに、プレスリリース、製品のお知らせ、キャンペーン情報を表示します。

## 構成

- `app.py`: Flask アプリケーション本体
- `templates/`: HTML テンプレート
- `static/`: CSS
- `sql/01_schema.sql`: テーブル作成
- `sql/02_seed.sql`: 初期データ投入
- `sql/03_drop.sql`: テーブル削除
- `deploy/oci-training-app.service`: systemd サービス定義例
- `.env.example`: 環境変数の設定例

## 対応 OS

OCI Compute の Oracle Linux 8 / 9 / 10 を対象にします。

Oracle Linux 8 と 9 は、研修時点で利用可能な最新マイナーバージョンを使う前提です。旧マイナーバージョンは考慮しません。

アプリケーションは Python 3.12 の仮想環境で実行します。OS のバージョンによっては、Python 3.12 の追加インストールが必要な場合もあります。

| OS | Python |
| --- | --- |
| Oracle Linux 8 最新版 | `python3.12` を追加インストール |
| Oracle Linux 9 最新版 | `python3.12` を追加インストール |
| Oracle Linux 10 最新版 | 標準の `python3` が Python 3.12 |

## 全体のデプロイ手順

1. DB 接続用クライアントツールを用意する
2. DB ユーザー、テーブル、初期データを作成する
3. Web サーバーに Python 3.12 とアプリケーションを配置する
4. systemd でアプリケーションを起動する
5. OS ファイアウォール、OCI Security List または NSG、Load Balancer を設定する
6. `/health` と `/db-health` で動作確認する

## DB 接続用クライアントツール

DB 初期化 SQL を実行するため、SQLcl または SQL*Plus を用意します。推奨は SQLcl です。

DB に到達できるマシンで実行する必要があるので、そのマシンに SQLcl または SQL*Plus をインストールします。

### 推奨: SQLcl をインストールする

SQLcl は SQL*Plus 互換のコマンドも多く利用できる Oracle のコマンドラインツールです。

```bash
sudo dnf install -y java-17-openjdk unzip curl
curl -L -o /tmp/sqlcl-latest.zip https://download.oracle.com/otn_software/java/sqldeveloper/sqlcl-latest.zip
sudo unzip -q /tmp/sqlcl-latest.zip -d /opt
sudo ln -sfn /opt/sqlcl/bin/sql /usr/local/bin/sql
sql -version
```

DB に接続できることを確認します。

```bash
sql training_app/ChangeMe_12345@'<DB_HOST>:1521/<SERVICE_NAME>'
```

まだ `training_app` ユーザーを作成していない場合、この接続確認は DB 管理者ユーザーで行ってください。

SQL*Plus をインストールする場合、公式ドキュメントを参照してください。以降の手順は、SQLcl を前提に説明します。

## DB 初期化

DB 管理者ユーザーでアプリ用ユーザーを作成します。パスワードは研修環境に合わせて変更してください。

```bash
sql '<ADMIN_USER>/<ADMIN_PASSWORD>@<DB_HOST>:1521/<SERVICE_NAME>'
```

接続後に以下を実行します。

```sql
create user training_app identified by "ChangeMe_12345";
grant create session, create table, create sequence to training_app;
alter user training_app quota unlimited on users;
exit
```

次に、DB 初期化を実行するマシンに、`sql/` ディレクトリ内の SQL スクリプトを配置してください。

アプリ用ユーザーでスキーマ作成と初期データ投入を実行します。

```bash
sql training_app/ChangeMe_12345@'<DB_HOST>:1521/<SERVICE_NAME>' @sql/01_schema.sql
sql training_app/ChangeMe_12345@'<DB_HOST>:1521/<SERVICE_NAME>' @sql/02_seed.sql
```

初期化し直す場合:

```bash
sql training_app/ChangeMe_12345@'<DB_HOST>:1521/<SERVICE_NAME>' @sql/03_drop.sql
sql training_app/ChangeMe_12345@'<DB_HOST>:1521/<SERVICE_NAME>' @sql/01_schema.sql
sql training_app/ChangeMe_12345@'<DB_HOST>:1521/<SERVICE_NAME>' @sql/02_seed.sql
```

## Web サーバーへのデプロイ

### 1. SSH 接続

```bash
ssh opc@<WEB_SERVER_PUBLIC_OR_PRIVATE_IP>
```

### 2. OS 確認

```bash
cat /etc/oracle-release
```

### 3. Python 3.12 と Git の導入

Oracle Linux 8 / 9:

```bash
sudo dnf install -y curl python3.12 python3.12-pip python3.12-setuptools python3.12-wheel git
python3.12 --version
```

Oracle Linux 10:

```bash
sudo dnf install -y curl python3 python3-pip python3-setuptools python3-wheel git
python3 --version
```

以降の手順では、`python3.12` の前提で説明します。Oracle Linux 10 の場合は、`python3.12` を `python3` と読み替えてください。

### 4. アプリケーション配置

ソースコード一式を `/opt/oci-training-app` に配置します。

```bash
sudo mkdir -p /opt/oci-training-app
sudo chown opc:opc /opt/oci-training-app
cd /opt/oci-training-app
```

Git を使う場合:

```bash
git clone <REPOSITORY_URL> /opt/oci-training-app
cd /opt/oci-training-app
```

zip ファイル等で配布された場合は、展開後に `/opt/oci-training-app` へ配置してください。

### 5. Python 仮想環境と依存ライブラリ

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

### 6. 環境変数ファイル

```bash
cp .env.example .env
vi .env
```

設定例:

```env
APP_NAME=OCI Training Public Site
FLASK_HOST=0.0.0.0
FLASK_PORT=8000
DB_USER=training_app
DB_PASSWORD=ChangeMe_12345
DB_DSN=<DB_PRIVATE_IP>:1521/<SERVICE_NAME>
```

`DB_DSN` には、Web サーバーから到達できる DB のプライベート IP またはホスト名を指定します。

### 7. systemd 登録

```bash
sudo cp deploy/oci-training-app.service /etc/systemd/system/oci-training-app.service
sudo systemctl daemon-reload
sudo systemctl enable --now oci-training-app
sudo systemctl status oci-training-app
```

### 8. OS ファイアウォール

OCI の Oracle Linux イメージでは、通常 `firewalld` が有効です。アプリケーションの待受ポートを開放します。

```bash
sudo firewall-cmd --permanent --add-port=8000/tcp
sudo firewall-cmd --reload
sudo firewall-cmd --list-ports
```

OCI 側でも必要な通信を許可してください。

## 動作確認

Web サーバー上でローカルで確認する場合:

```bash
curl -i http://localhost:8000/health
curl -i http://localhost:8000/db-health
curl -i http://localhost:8000/
```

| パス | 説明 |
| --- | --- |
| / | アプリケーションのメイン画面 |
| /health | Web サーバーのヘルスチェック用 URL（アプリケーションプロセス確認） |
| /db-health | Web サーバーから DB への接続をチェックするための URL（DB 疎通確認） |


## トラブルシューティング

サービスログ:

```bash
sudo journalctl -u oci-training-app -f
```

## cloud-init で初期インストールを自動化する場合

Compute 作成時の cloud-init で初期パッケージだけ導入しておくと、OS ログイン後の作業を短縮できます。

Oracle Linux 8 / 9 用:

```yaml
#cloud-config
package_update: true
packages:
  - python3.12
  - python3.12-pip
  - python3.12-setuptools
  - python3.12-wheel
  - git
  - curl
  - java-17-openjdk
  - unzip
runcmd:
  - [ firewall-cmd, --permanent, --add-port=8000/tcp ]
  - [ firewall-cmd, --reload ]
```

Oracle Linux 10 用:

```yaml
#cloud-config
package_update: true
packages:
  - python3
  - python3-pip
  - python3-setuptools
  - python3-wheel
  - git
  - curl
  - java-17-openjdk
  - unzip
runcmd:
  - [ firewall-cmd, --permanent, --add-port=8000/tcp ]
  - [ firewall-cmd, --reload ]
```

アプリケーションの配置、`.env` の作成、systemd 登録、SQLcl の導入まで cloud-init や Terraform `user_data` で自動化しても構いません。ただし、DB パスワードを Terraform state や cloud-init ログに平文で残さないよう注意してください。

## 注意事項

- DB 接続情報やパスワードは Terraform state に平文で残さないでください。
- このアプリケーションは研修用サンプルです。認証、管理画面、入力機能は実装していません。

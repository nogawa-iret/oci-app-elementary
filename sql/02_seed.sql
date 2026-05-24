whenever sqlerror exit sql.sqlcode

insert into categories (category_code, category_name, display_order)
values ('press', 'プレスリリース', 10);

insert into categories (category_code, category_name, display_order)
values ('product', '製品のお知らせ', 20);

insert into categories (category_code, category_name, display_order)
values ('campaign', 'キャンペーン', 30);

insert into public_contents (
    category_id,
    title,
    summary,
    body,
    status,
    published_at
)
select
    category_id,
    '新サービス提供開始のお知らせ',
    '法人向けクラウド連携サービスの提供を開始しました。',
    '当社は、既存システムとクラウドサービスを安全に連携する法人向けサービスの提供を開始しました。' || chr(10) ||
    '本サービスにより、段階的なクラウド移行と運用負荷の軽減を支援します。',
    'PUBLISHED',
    timestamp '2026-05-10 09:00:00'
from categories
where category_code = 'press';

insert into public_contents (
    category_id,
    title,
    summary,
    body,
    status,
    published_at
)
select
    category_id,
    'サポートポータル機能追加',
    'お客様向けサポートポータルに問い合わせ履歴の検索機能を追加しました。',
    'サポートポータルで過去の問い合わせ履歴を検索できるようになりました。' || chr(10) ||
    'カテゴリ、受付日、対応状況で絞り込みができます。',
    'PUBLISHED',
    timestamp '2026-05-15 10:30:00'
from categories
where category_code = 'product';

insert into public_contents (
    category_id,
    title,
    summary,
    body,
    status,
    published_at
)
select
    category_id,
    '初期導入支援キャンペーン',
    '対象サービスを新規契約いただいたお客様に初期導入支援を提供します。',
    'キャンペーン期間中に対象サービスをご契約いただいたお客様へ、初期設定と運用設計の支援を提供します。' || chr(10) ||
    '詳細は営業担当までお問い合わせください。',
    'PUBLISHED',
    timestamp '2026-05-20 13:00:00'
from categories
where category_code = 'campaign';

insert into public_contents (
    category_id,
    title,
    summary,
    body,
    status,
    published_at
)
select
    category_id,
    '公開前の記事サンプル',
    'このデータは画面に表示されません。',
    'status が DRAFT のため、アプリケーションの一覧には表示されません。',
    'DRAFT',
    timestamp '2026-05-22 12:00:00'
from categories
where category_code = 'press';

commit;

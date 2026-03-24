# Generated manually — fix varchar(10) → varchar(20) + add perf indexes

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('g2b', '0006_bc61_status_and_new_fields'),
    ]

    operations = [
        # --- varchar(10) → varchar(20) 강제 수정 (Django state는 이미 20이라 RunSQL 필요) ---
        migrations.RunSQL(
            sql="""
                ALTER TABLE g2b_bidannouncement
                    ALTER COLUMN a_value_status TYPE varchar(20),
                    ALTER COLUMN base_amount_status TYPE varchar(20);
            """,
            reverse_sql="""
                ALTER TABLE g2b_bidannouncement
                    ALTER COLUMN a_value_status TYPE varchar(10),
                    ALTER COLUMN base_amount_status TYPE varchar(10);
            """,
        ),
        # --- 유사 공고 통계 쿼리 성능 인덱스 ---
        migrations.AddIndex(
            model_name='bidcontract',
            index=models.Index(
                fields=['presume_price', 'openg_date'],
                name='idx_contract_price_date',
            ),
        ),
        migrations.AddIndex(
            model_name='bidresult',
            index=models.Index(
                fields=['bid_ntce_no', 'bid_ntce_ord', 'openg_rank'],
                name='idx_result_ntce_rank',
            ),
        ),
    ]

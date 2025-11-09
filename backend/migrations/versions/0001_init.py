from alembic import op
import sqlalchemy as sa

revision = '0001_init'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('raw_sales',
                    sa.Column('id', sa.Integer(), primary_key=True),
                    sa.Column('source', sa.String(length=50), nullable=False),
                    sa.Column('raw_json', sa.Text(), nullable=False),
                    sa.Column('created_at', sa.DateTime(timezone=True),
                              server_default=sa.func.now())
                    )

    op.create_table('normalized_sales',
                    sa.Column('id', sa.Integer(), primary_key=True),
                    sa.Column('date', sa.Date(), nullable=False),
                    sa.Column('invoice_number', sa.String(
                        length=100), nullable=False),
                    sa.Column('customer', sa.String(length=255)),
                    sa.Column('product', sa.String(
                        length=255), nullable=False),
                    sa.Column('quantity', sa.Float(), nullable=False),
                    sa.Column('unit_price_net', sa.Numeric(
                        18, 2), nullable=False),
                    sa.Column('vat_rate', sa.Float(), nullable=False),
                    sa.Column('net_amount', sa.Numeric(18, 2), nullable=False),
                    sa.Column('vat_amount', sa.Numeric(18, 2), nullable=False),
                    sa.Column('gross_amount', sa.Numeric(
                        18, 2), nullable=False),
                    sa.Column('payment_method', sa.String(
                        length=50), nullable=False),
                    sa.Column('created_at', sa.DateTime(timezone=True),
                              server_default=sa.func.now())
                    )
    op.create_index('ix_normalized_sales_date', 'normalized_sales', ['date'])
    op.create_index('ix_normalized_sales_invoice',
                    'normalized_sales', ['invoice_number'])

    op.create_table('bank_tx',
                    sa.Column('id', sa.Integer(), primary_key=True),
                    sa.Column('date', sa.Date(), nullable=False),
                    sa.Column('description', sa.Text(), nullable=False),
                    sa.Column('debit', sa.Numeric(18, 2)),
                    sa.Column('credit', sa.Numeric(18, 2)),
                    sa.Column('balance', sa.Numeric(18, 2)),
                    sa.Column('tx_type', sa.String(length=50)),
                    sa.Column('created_at', sa.DateTime(timezone=True),
                              server_default=sa.func.now())
                    )
    op.create_index('ix_bank_tx_date', 'bank_tx', ['date'])
    op.create_index('ix_bank_tx_tx_type', 'bank_tx', ['tx_type'])

    op.create_table('reconciliation_cache',
                    sa.Column('id', sa.Integer(), primary_key=True),
                    sa.Column('date', sa.Date(), nullable=False),
                    sa.Column('sales_card', sa.Numeric(18, 2), nullable=False),
                    sa.Column('bank_tpa', sa.Numeric(18, 2), nullable=False),
                    sa.Column('fees', sa.Numeric(18, 2), nullable=False),
                    sa.Column('delta', sa.Numeric(18, 2), nullable=False),
                    sa.Column('detail_json', sa.Text(), nullable=False),
                    sa.Column('created_at', sa.DateTime(timezone=True),
                              server_default=sa.func.now())
                    )
    op.create_index('ix_recon_date', 'reconciliation_cache', ['date'])


def downgrade():
    op.drop_index('ix_recon_date', table_name='reconciliation_cache')
    op.drop_table('reconciliation_cache')
    op.drop_index('ix_bank_tx_tx_type', table_name='bank_tx')
    op.drop_index('ix_bank_tx_date', table_name='bank_tx')
    op.drop_table('bank_tx')
    op.drop_index('ix_normalized_sales_invoice', table_name='normalized_sales')
    op.drop_index('ix_normalized_sales_date', table_name='normalized_sales')
    op.drop_table('normalized_sales')
    op.drop_table('raw_sales')

"""create users table

Revision ID: 01_create_users_table
Revises: 
Create Date: 2024-02-13 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '01_create_users_table'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Создаем таблицу пользователей
    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()')),
    )
    op.create_index('users_id_idx', 'users', ['id'])
    op.create_index('users_email_idx', 'users', ['email'])

    # Добавляем внешний ключ в таблицу notification_messages
    op.drop_table('notification_messages')
    op.create_table(
        'notification_messages',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('film_id', postgresql.UUID(as_uuid=True)),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    )
    op.create_index('notifications_id_idx', 'notification_messages', ['id'])
    op.create_index('notifications_user_id_idx', 'notification_messages', ['user_id'])


def downgrade():
    # Удаляем внешний ключ и индексы из таблицы notification_messages
    op.drop_index('notifications_user_id_idx', 'notification_messages')
    op.drop_index('notifications_id_idx', 'notification_messages')
    op.drop_table('notification_messages')
    
    # Воссоздаем таблицу notification_messages без внешнего ключа
    op.create_table(
        'notification_messages',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('film_id', postgresql.UUID(as_uuid=True)),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()')),
    )
    op.create_index('notifications_id_idx', 'notification_messages', ['id'])
    
    # Удаляем таблицу пользователей
    op.drop_index('users_email_idx', 'users')
    op.drop_index('users_id_idx', 'users')
    op.drop_table('users') 
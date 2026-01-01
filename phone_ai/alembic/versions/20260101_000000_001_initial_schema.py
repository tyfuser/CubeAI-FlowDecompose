"""Initial schema for video shooting assistant

Revision ID: 001
Revises: 
Create Date: 2026-01-01 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create analysis_tasks table
    op.create_table(
        'analysis_tasks',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('video_id', sa.String(255), nullable=False),
        sa.Column('status', sa.String(50), nullable=False, server_default='pending'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('uploader_output', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('feature_output', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('heuristic_output', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('metadata_output', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('instruction_card', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.CheckConstraint(
            "status IN ('pending', 'processing', 'completed', 'failed')",
            name='valid_status'
        ),
    )
    op.create_index('idx_tasks_status', 'analysis_tasks', ['status'])
    op.create_index('idx_tasks_video_id', 'analysis_tasks', ['video_id'])
    
    # Create user_feedback table
    op.create_table(
        'user_feedback',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('task_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('instruction_index', sa.Integer(), nullable=True),
        sa.Column('action', sa.String(50), nullable=False),
        sa.Column('rating', sa.Integer(), nullable=True),
        sa.Column('comment', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['task_id'], ['analysis_tasks.id']),
        sa.CheckConstraint('rating >= 1 AND rating <= 5', name='valid_rating'),
    )
    op.create_index('idx_feedback_task_id', 'user_feedback', ['task_id'])
    
    # Create reference_videos table
    op.create_table(
        'reference_videos',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('video_path', sa.String(500), nullable=False),
        sa.Column('motion_type', sa.String(50), nullable=True),
        sa.Column('subject_type', sa.String(100), nullable=True),
        sa.Column('embedding_id', sa.String(255), nullable=True),
        sa.Column('video_metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('idx_reference_motion_type', 'reference_videos', ['motion_type'])


def downgrade() -> None:
    op.drop_index('idx_reference_motion_type', table_name='reference_videos')
    op.drop_table('reference_videos')
    
    op.drop_index('idx_feedback_task_id', table_name='user_feedback')
    op.drop_table('user_feedback')
    
    op.drop_index('idx_tasks_video_id', table_name='analysis_tasks')
    op.drop_index('idx_tasks_status', table_name='analysis_tasks')
    op.drop_table('analysis_tasks')

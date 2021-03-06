"""empty message

Revision ID: ae811134a7ad
Revises: None
Create Date: 2016-10-15 23:09:18.355887

"""

# revision identifiers, used by Alembic.
revision = 'ae811134a7ad'
down_revision = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.create_table('boats',
    sa.Column('id', sa.Integer(), nullable=False, autoincrement=True),
    sa.Column('is_seabus', sa.Boolean(), nullable=True),
    sa.Column('mmsi', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=120), nullable=True),
    sa.Column('dim_to_bow', sa.Integer(), nullable=True),
    sa.Column('dim_to_stern', sa.Integer(), nullable=True),
    sa.Column('dim_to_port', sa.Integer(), nullable=True),
    sa.Column('dim_to_star', sa.Integer(), nullable=True),
    sa.Column('type_and_cargo', sa.Integer(), nullable=True),
    sa.Column('lastseen_on', sa.DateTime(), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('mmsi')
    )
    op.create_table('telemetry',
    sa.Column('id', sa.Integer(), nullable=False, autoincrement=True),
    sa.Column('boat_id', sa.Integer(), nullable=True),
    sa.Column('nav_status', sa.Integer(), nullable=True),
    sa.Column('pos_accuracy', sa.Integer(), nullable=True),
    sa.Column('lon', sa.Float(), nullable=True),
    sa.Column('lat', sa.Float(), nullable=True),
    sa.Column('speed_over_ground', sa.Float(), nullable=True),
    sa.Column('course_over_ground', sa.Float(), nullable=True),
    sa.Column('true_heading', sa.Integer(), nullable=True),
    sa.Column('rate_of_turn', sa.Float(), nullable=True),
    sa.Column('rate_of_turn_over_range', sa.Boolean(), nullable=True),
    sa.Column('timestamp', sa.Integer(), nullable=True),
    sa.Column('received', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['boat_id'], ['boats.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('telemetry')
    op.drop_table('boats')
    ### end Alembic commands ###

from typing import Annotated, List, TYPE_CHECKING
from sqlalchemy import String, Text, BigInteger, Integer, Boolean, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from bot.models.base import Base
from bot.models.fields import bigint_pk, timestamp, is_deleted, text_field

if TYPE_CHECKING:
    from bot.models.account import Account

class User(Base):
    """用户模型"""
    __tablename__ = 'users'
    
    # 主键ID
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    
    # Telegram用户ID
    telegram_id: Mapped[int] = mapped_column(BigInteger, nullable=False, unique=True, index=True)
    
    # Telegram用户名
    username: Mapped[str | None] = mapped_column(String(64), nullable=True)
    
    # Telegram名字
    first_name: Mapped[str | None] = mapped_column(String(64), nullable=True)
    
    # Telegram姓氏
    last_name: Mapped[str | None] = mapped_column(String(64), nullable=True)
    
    # 语言代码
    language_code: Mapped[str | None] = mapped_column(String(10), nullable=True)
    
    # 是否为Telegram高级用户
    is_premium: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    
    # 加入来源(1:私聊机器人 2:群组)
    join_source: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    
    # 来源群组ID
    source_group_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    
    # 状态(1:正常 2:禁用)
    status: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    
    # 最后活跃时间
    last_active_time: Mapped[timestamp | None] = mapped_column(nullable=True)
    
    # 备注
    remarks: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    # 关联账户
    accounts: Mapped[List["Account"]] = relationship("Account", back_populates="user")
    
    # 关联群组成员
    group_members: Mapped[List["TgGroupMember"]] = relationship("TgGroupMember", back_populates="user")

    def __repr__(self):
        return f"<User(id={self.id}, telegram_id={self.telegram_id}, username={self.username})>"

    @property
    def full_name(self):
        """获取用户全名"""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.first_name or self.username or str(self.telegram_id)

    @property
    def status_name(self):
        """获取状态名称"""
        status_map = {
            1: "正常",
            2: "禁用"
        }
        return status_map.get(self.status, "未知")

    @property
    def join_source_name(self):
        """获取加入来源名称"""
        source_map = {
            1: "私聊机器人",
            2: "群组"
        }
        return source_map.get(self.join_source, "未知")


class TgGroup(Base):
    """Telegram群组模型"""
    __tablename__ = 'tg_groups'

    # 主键ID
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    
    # Telegram群组ID
    telegram_id: Mapped[int] = mapped_column(BigInteger, nullable=False, unique=True, index=True)
    
    # 群组名称
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    
    # 群组用户名
    username: Mapped[str | None] = mapped_column(String(64), nullable=True)
    
    # 成员数量
    member_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    
    # 机器人角色(member/admin)
    bot_role: Mapped[str] = mapped_column(String(20), nullable=False, default='member')
    
    # 类型(group:群组 channel:频道)
    type: Mapped[str] = mapped_column(String(20), nullable=False, default='group')
    
    # 状态(1:正常 2:已退出 3:被踢出)
    status: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    
    # 群组设置
    settings: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    # 备注
    remarks: Mapped[text_field]
    
    # 关联群组成员
    members: Mapped[List["TgGroupMember"]] = relationship("TgGroupMember", back_populates="group")

    def __repr__(self):
        return f"<TgGroup(id={self.id}, telegram_id={self.telegram_id}, title={self.title})>"

    @property
    def status_name(self):
        """获取状态名称"""
        status_map = {
            1: "正常",
            2: "已退出",
            3: "被踢出"
        }
        return status_map.get(self.status, "未知")

    @property
    def type_name(self):
        """获取类型名称"""
        type_map = {
            'group': "群组",
            'channel': "频道"
        }
        return type_map.get(self.type, "未知")


class TgGroupMember(Base):
    """群组成员模型"""
    __tablename__ = 'tg_group_members'

    # 主键ID
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    
    # 群组ID
    group_id: Mapped[int] = mapped_column(BigInteger, ForeignKey('tg_groups.id'), nullable=False)
    
    # 用户ID
    user_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey('users.id'), nullable=True)
    
    # Telegram用户ID
    telegram_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    
    # 群内昵称
    nickname: Mapped[str | None] = mapped_column(String(64), nullable=True)
    
    # 角色(member/admin/creator)
    role: Mapped[str] = mapped_column(String(20), nullable=False, default='member')
    
    # 权限设置
    permissions: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    # 加入时间
    join_time: Mapped[timestamp]
    
    # 最后活跃时间
    last_active_time: Mapped[timestamp | None] = mapped_column(nullable=True)
    
    # 状态(1:正常 2:已退出 3:被踢出)
    status: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    
    # 备注
    remarks: Mapped[text_field]
    
    # 关联用户
    user: Mapped["User"] = relationship("User", back_populates="group_members")
    
    # 关联群组
    group: Mapped["TgGroup"] = relationship("TgGroup", back_populates="members")

    def __repr__(self):
        return f"<TgGroupMember(id={self.id}, group_id={self.group_id}, telegram_id={self.telegram_id})>"

    @property
    def status_name(self):
        """获取状态名称"""
        status_map = {
            1: "正常",
            2: "已退出",
            3: "被踢出"
        }
        return status_map.get(self.status, "未知")


class TgGroupCommand(Base):
    """群组命令表"""
    __tablename__ = 'tg_group_commands'
    
    # 主键ID
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    
    # 群组ID
    group_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    
    # 命令名称
    command: Mapped[str] = mapped_column(String(32), nullable=False)
    
    # 命令描述
    description: Mapped[str | None] = mapped_column(String(255), nullable=True)
    
    # 处理函数
    handler: Mapped[str] = mapped_column(String(64), nullable=False)
    
    # 是否启用
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    # 使用权限
    permissions: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    
    # 备注
    remarks: Mapped[text_field]

    def __repr__(self):
        return f"<TgGroupCommand(id={self.id}, group_id={self.group_id}, command={self.command})>" 
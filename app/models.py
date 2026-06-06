from sqlalchemy.orm import declarative_base, Mapped, mapped_column, relationship
from sqlalchemy import String, Integer, DateTime, func, Float, JSON, ForeignKey
import uuid
from sqlalchemy.dialects.postgresql import UUID

Base = declarative_base()


class Conversation(Base):
    __tablename__ = "conversations"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user: Mapped[str] = mapped_column(String(64), index=True)
    created_at: Mapped = mapped_column(DateTime(timezone=True), server_default=func.now())

    # messages relationship (not eager-loaded by default)
    messages = relationship("Message", back_populates="conversation")


class Message(Base):
    __tablename__ = "messages"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("conversations.id"), nullable=True, index=True)
    provider: Mapped[str] = mapped_column(String(32), index=True)
    provider_message_id: Mapped[str] = mapped_column(String(128), index=True, nullable=True)
    from_number: Mapped[str] = mapped_column(String(64), index=True)
    to_number: Mapped[str] = mapped_column(String(64), nullable=True)
    type: Mapped[str] = mapped_column(String(32), index=True)
    text: Mapped[str] = mapped_column(String, nullable=True)
    media: Mapped = mapped_column(JSON, nullable=True)
    lang: Mapped[str] = mapped_column(String(8), nullable=True)
    urgency: Mapped[str] = mapped_column(String(16), nullable=True)
    score: Mapped[float] = mapped_column(Float, nullable=True)
    is_bot: Mapped[bool] = mapped_column(Integer, default=0)
    created_at: Mapped = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)

    conversation = relationship("Conversation", back_populates="messages")


class ModelArtifact(Base):
    __tablename__ = "model_artifacts"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(128), index=True)
    version: Mapped[str] = mapped_column(String(64), index=True)
    path: Mapped[str] = mapped_column(String(256))
    metadata: Mapped = mapped_column(JSON, nullable=True)
    created_at: Mapped = mapped_column(DateTime(timezone=True), server_default=func.now())


class DeliveryReceipt(Base):
    __tablename__ = "delivery_receipts"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    message_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("messages.id"), nullable=True)
    provider: Mapped[str] = mapped_column(String(32))
    provider_message_id: Mapped[str] = mapped_column(String(128), nullable=True)
    status: Mapped[str] = mapped_column(String(32), index=True)
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped = mapped_column(DateTime(timezone=True), server_default=func.now())

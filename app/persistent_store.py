from typing import List, Dict, Any, Optional
from app.db import AsyncSessionLocal
from app.models import Conversation, Message
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
import uuid


class PersistentStore:
    """Simple persistent store using Postgres / SQLAlchemy async.

    This complements or replaces the Redis ConvoStore for durable storage of messages and artifacts.
    """

    def __init__(self):
        pass

    async def append_message(self, from_number: str, message: Dict[str, Any]) -> Dict[str, Any]:
        async with AsyncSessionLocal() as session:  # type: AsyncSession
            # find or create conversation for this user
            stmt = select(Conversation).where(Conversation.user == from_number)
            res = await session.execute(stmt)
            conv = res.scalars().first()
            if not conv:
                conv = Conversation(user=from_number)
                session.add(conv)
                await session.flush()
            # create message
            msg = Message(
                conversation_id=conv.id,
                provider=message.get('provider', ''),
                provider_message_id=message.get('message_id'),
                from_number=from_number,
                to_number=message.get('to'),
                type=message.get('type', 'text'),
                text=message.get('text'),
                media=message.get('media'),
                lang=message.get('lang'),
                urgency=message.get('urgency'),
                score=message.get('score'),
                is_bot=1 if message.get('is_bot') else 0,
            )
            session.add(msg)
            await session.commit()
            return {"id": str(msg.id), "conversation_id": str(conv.id)}

    async def get_history(self, from_number: str, limit: int = 10) -> List[Dict[str, Any]]:
        async with AsyncSessionLocal() as session:
            stmt = select(Conversation).where(Conversation.user == from_number)
            res = await session.execute(stmt)
            conv = res.scalars().first()
            if not conv:
                return []
            msg_stmt = select(Message).where(Message.conversation_id == conv.id).order_by(Message.created_at.desc()).limit(limit)
            msgs = await session.execute(msg_stmt)
            out = []
            for m in msgs.scalars().all():
                out.append({
                    "text": m.text,
                    "type": m.type,
                    "lang": m.lang,
                    "created_at": m.created_at.isoformat() if m.created_at else None,
                })
            return out

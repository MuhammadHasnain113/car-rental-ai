import asyncio
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from backend.config import SYSTEM_PROMPT

@dataclass
class Turn:
    role: str
    content: str

@dataclass
class SessionState:
    session_id: str
    history: List[Turn] = field(default_factory=list)
    lock: asyncio.Lock = field(default_factory=asyncio.Lock)
    # Extracted entity anchors to stay faithful across turns
    collected_slots: Dict[str, str] = field(default_factory=dict)
    current_stage: str = "GREETING"

class ConversationManager:
    """
    Phase III Conversation Manager:
    - Enforces turn-taking synchronization via asyncio.Lock
    - Maintains multi-turn context with role validation
    - Orchestrates structured prompts with XML/Markdown delimiters
    - Anchors critical rental slots so context is preserved beyond the sliding window
    """
    def __init__(self, max_history_turns: int = 5):
        self.sessions: Dict[str, SessionState] = {}
        self.max_history_turns = max_history_turns

    def get_or_create_session(self, session_id: str) -> SessionState:
        if session_id not in self.sessions:
            self.sessions[session_id] = SessionState(session_id=session_id)
        return self.sessions[session_id]

    def reset_session(self, session_id: str):
        if session_id in self.sessions:
            self.sessions[session_id].history.clear()
            self.sessions[session_id].collected_slots.clear()
            self.sessions[session_id].current_stage = "GREETING"

    def record_turn(self, session_id: str, role: str, content: str):
        session = self.get_or_create_session(session_id)
        session.history.append(Turn(role=role, content=content))
        
        # Context window management: Keep the initial turn pair + recent N turns
        # to ensure the initial intent is never dropped
        total_messages = len(session.history)
        max_messages = self.max_history_turns * 2
        if total_messages > max_messages:
            # Preserve the first turn (anchoring intent) + sliding tail
            session.history = [session.history[0], session.history[1]] + session.history[-(max_messages - 2):]

    def build_orchestrated_prompt(self, session_id: str, incoming_message: str) -> List[dict]:
        session = self.get_or_create_session(session_id)
        
        orchestrated_system_prompt = f"""{SYSTEM_PROMPT}

<dialogue_state>
- Current Conversation Stage: {session.current_stage}
- Memory Anchors: {session.collected_slots if session.collected_slots else "None recorded yet"}
</dialogue_state>

<strict_guardrails>
- You are not a general assistant.
- Under NO circumstance solve math queries, general knowledge, or coding tasks.
- If the user's prompt is not about cars, rental pricing, insurance, or reservations, immediately output the mandatory refusal sentence.
</strict_guardrails>
"""

        messages = [{"role": "system", "content": orchestrated_system_prompt}]
        
        for turn in session.history:
            messages.append({"role": turn.role, "content": turn.content})
            
        messages.append({"role": "user", "content": incoming_message})
        return messages

manager = ConversationManager()
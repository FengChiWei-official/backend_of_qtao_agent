from src.modules.dbController.dao.dialogue_record_dao import DialogueRecordDAO
from src.modules.dbController.models.record import DialogueRecord
from src.modules.services.dto.dto import DialogueRecordDTO
import uuid
from typing import List
from datetime import datetime

class DialogueRecordBusiness:
    def __init__(self, config: dict):
        self.dialogue_record_dao = DialogueRecordDAO(config)

    def create_record(
        self,
        conversation_id: str,
        user_id: str,
        user_query: str,
        system_response: str,
        system_thoughts: str | None = None,
        image_list: list[str] | None = None,
        query_sent_at: datetime | None = None,
        response_received_at: datetime | None = None
    ) -> DialogueRecordDTO:
        if not conversation_id or not user_id or not user_query or not system_response:
            raise ValueError("conversation_id, user_id, user_query, system_response are required.")
        record = DialogueRecord(
            id=str(uuid.uuid4()),
            conversation_id=conversation_id,
            user_id=user_id,
            user_query=user_query,
            system_response=system_response,
            system_thoughts=system_thoughts,
            image_list=image_list,
            query_sent_at=query_sent_at or datetime.utcnow(),
            response_received_at=response_received_at or datetime.utcnow(),
            created_at=datetime.utcnow()
        )
        try:
            record = self.dialogue_record_dao.create_dialogue_record(record)
        except (LookupError, ValueError, AttributeError) as e:
            raise e
        return DialogueRecordDTO.from_obj(record)

    def get_record(self, record_id: str) -> DialogueRecordDTO:
        record = self.dialogue_record_dao.get_record_by_record_id(record_id)
        return DialogueRecordDTO.from_obj(record)

    def update_record(self, record_id: str, **kwargs) -> DialogueRecordDTO:
        record = self.dialogue_record_dao.get_record_by_record_id(record_id)
        for key, value in kwargs.items():
            if hasattr(record, key):
                setattr(record, key, value)
        record = self.dialogue_record_dao.update_dialogue_record(record)
        return DialogueRecordDTO.from_obj(record)

    def delete_record(self, record_id: str, is_hard_delete: bool = False) -> None:
        self.dialogue_record_dao.delete_dialogue_record(record_id, is_hard_delete)

    def list_records_by_conversation(self, conversation_id: str, last_n: int | None = None) -> List[DialogueRecordDTO]:

        records = self.dialogue_record_dao.get_records_by_conversation_id(conversation_id, last_n=last_n)
        return [DialogueRecordDTO.from_obj(r) for r in records]

from sqlalchemy import Column, Integer, String, BigInteger, Text
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)

    # Channel Identifiers
    source = Column(String, nullable=False)  # Input username/link
    source_id = Column(BigInteger, nullable=True) # Resolved ID

    target = Column(String, nullable=False)
    target_id = Column(BigInteger, nullable=True)

    # Task-Specific Replacements (Legacy/Granular support)
    find_user = Column(String, nullable=True)
    replace_user = Column(String, nullable=True)
    find_link = Column(String, nullable=True)
    replace_link = Column(String, nullable=True)

    def __repr__(self):
        return f"<Task(id={self.id}, source={self.source}, target={self.target})>"

class GlobalRule(Base):
    __tablename__ = "global_rules"

    id = Column(Integer, primary_key=True, index=True)

    # Rule Definition
    rule_type = Column(String, nullable=False) # e.g., 'replace', 'block', 'filter'
    target_type = Column(String, nullable=False) # e.g., 'user', 'link', 'text'

    find_pattern = Column(Text, nullable=False)
    replace_with = Column(Text, nullable=True) # Can be replacement text or flags like SKIP_MESSAGE

    def __repr__(self):
        return f"<GlobalRule(type={self.rule_type}, target={self.target_type}, pattern={self.find_pattern})>"

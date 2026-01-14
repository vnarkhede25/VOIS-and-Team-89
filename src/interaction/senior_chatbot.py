import time
import random
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime

@dataclass
class ChatMessage:
    """Represents a chat message with context."""
    timestamp: str
    message: str
    sender: str  # 'user' or 'bot'
    context: str  # 'wellbeing', 'emergency', 'general'
    tone: str  # 'gentle', 'concerned', 'reassuring'

class SeniorChatbot:
    """
    Simple chatbot logic layer for senior citizen interaction.
    
    Features:
    - Wellbeing questions after events
    - Response logging for context
    - Elderly-friendly tone adaptation
    - No NLP API integration
    """
    
    def __init__(self):
        """Initialize the senior chatbot."""
        self.conversation_history: List[ChatMessage] = []
        self.current_context = "general"
        self.current_tone = "gentle"
        self.wellbeing_questions_asked = 0
        self.max_wellbeing_questions = 3
        
        # Elderly-friendly response templates
        self.response_templates = {
            'greeting': [
                "Hello! How are you feeling today?",
                "Good day! I'm here to help you.",
                "Hi there! Is everything alright?",
                "Hello! Nice to see you. How can I help?"
            ],
            'wellbeing': [
                "Are you feeling okay? Please tell me how you're doing.",
                "I'm checking in to see how you're feeling. Are you comfortable?",
                "Can you tell me if you're experiencing any pain or discomfort?",
                "I want to make sure you're alright. How are you feeling right now?"
            ],
            'concern': [
                "I'm a bit concerned. Are you sure you're okay?",
                "Please tell me if you need any help. I'm here for you.",
                "I want to make sure you're safe. Can you tell me how you're feeling?",
                "Your wellbeing is important to me. Please let me know if you need assistance."
            ],
            'reassurance': [
                "That's good to hear! I'm here if you need anything.",
                "Wonderful! I'm glad you're doing well.",
                "That makes me happy to hear. I'm always here to help.",
                "Great! I'll keep checking in to make sure you stay safe."
            ],
            'emergency': [
                "I'm getting help for you right away. Please stay calm.",
                "Don't worry, help is on the way. I'm here with you.",
                "I'm contacting emergency services. Please try to stay comfortable.",
                "Help is coming. I'll stay with you until they arrive."
            ],
            'clarification': [
                "I want to make sure I understand. Could you tell me more?",
                "Could you help me understand better? I want to help you properly.",
                "I'm here to listen. Can you tell me a bit more about that?",
                "I want to make sure I understand your needs. Can you explain more?"
            ],
            'gratitude': [
                "Thank you for telling me. I appreciate your patience.",
                "I'm grateful you shared that with me. It helps me help you better.",
                "Thank you for letting me know. I'm here to support you.",
                "I appreciate you taking the time to tell me. I'm here to help."
            ]
        }
        
        # Keywords for understanding user responses
        self.positive_keywords = [
            'good', 'fine', 'okay', 'alright', 'well', 'great', 'happy',
            'comfortable', 'no pain', 'not hurt', 'feeling good', 'doing well'
        ]
        
        self.negative_keywords = [
            'bad', 'pain', 'hurt', 'uncomfortable', 'not okay', 'sad',
            'worried', 'scared', 'help', 'need assistance', 'not well',
            'dizzy', 'weak', 'tired', 'sick', 'unwell'
        ]
        
        self.emergency_keywords = [
            "emergency", "help me", "call 911", "urgent", "critical",
            "can't breathe", "chest pain", "fall", "injured", "bleeding",
            "very bad", "terrible", "extreme pain"
        ]
    
    def handle_event(self, event_type: str, context: Optional[Dict] = None) -> str:
        """
        Handle system events and initiate appropriate conversation.
        
        Args:
            event_type: Type of event ('fall_detected', 'alert_cancelled', 'morning_check')
            context: Additional context about the event
            
        Returns:
            str: Initial message to user
        """
        self.current_context = event_type
        
        if event_type == "fall_detected":
            self.current_tone = "concern"
            message = self._get_emergency_response()
        elif event_type == "alert_cancelled":
            self.current_tone = "reassuring"
            message = "I'm glad you're okay! I was worried about you."
        elif event_type == "morning_check":
            self.current_tone = "gentle"
            message = "Good morning! How did you sleep? Are you feeling well today?"
        elif event_type == "wellbeing_check":
            self.current_tone = "gentle"
            message = self._get_wellbeing_question()
        else:
            self.current_tone = "gentle"
            message = self._get_greeting()
        
        # Log the bot's message
        self._log_message(message, "bot", event_type, self.current_tone)
        return message
    
    def process_user_input(self, user_input: str) -> str:
        """
        Process user input and generate appropriate response.
        
        Args:
            user_input: User's message
            
        Returns:
            str: Bot's response
        """
        # Log user input
        self._log_message(user_input, "user", self.current_context, "neutral")
        
        # Analyze user input
        sentiment = self._analyze_sentiment(user_input)
        
        # Generate response based on sentiment and context
        if sentiment == "emergency":
            self.current_tone = "concern"
            response = self._get_emergency_response()
        elif sentiment == "negative":
            self.current_tone = "concern"
            response = self._get_concern_response()
        elif sentiment == "positive":
            self.current_tone = "reassuring"
            response = self._get_reassurance_response()
        else:
            self.current_tone = "gentle"
            response = self._get_clarification_response()
        
        # Log bot's response
        self._log_message(response, "bot", self.current_context, self.current_tone)
        return response
    
    def ask_wellbeing_question(self) -> str:
        """
        Ask a wellbeing question and track responses.
        
        Returns:
            str: Wellbeing question
        """
        if self.wellbeing_questions_asked >= self.max_wellbeing_questions:
            return "I'll check in with you again later. I'm here if you need anything."
        
        self.current_context = "wellbeing"
        self.current_tone = "gentle"
        question = self._get_wellbeing_question()
        
        # Log the question
        self._log_message(question, "bot", "wellbeing", "gentle")
        return question
    
    def get_conversation_summary(self) -> Dict:
        """
        Get a summary of the conversation for context.
        
        Returns:
            dict: Conversation summary
        """
        user_messages = [msg for msg in self.conversation_history if msg.sender == "user"]
        bot_messages = [msg for msg in self.conversation_history if msg.sender == "bot"]
        
        # Analyze user sentiment
        user_sentiments = [self._analyze_sentiment(msg.message) for msg in user_messages]
        sentiment_counts = {
            "positive": user_sentiments.count("positive"),
            "negative": user_sentiments.count("negative"),
            "neutral": user_sentiments.count("neutral"),
            "emergency": user_sentiments.count("emergency")
        }
        
        return {
            "total_messages": len(self.conversation_history),
            "user_messages": len(user_messages),
            "bot_messages": len(bot_messages),
            "current_context": self.current_context,
            "current_tone": self.current_tone,
            "wellbeing_questions_asked": self.wellbeing_questions_asked,
            "user_sentiment_distribution": sentiment_counts,
            "last_interaction": self.conversation_history[-1].timestamp if self.conversation_history else None
        }
    
    def _analyze_sentiment(self, text: str) -> str:
        """
        Simple sentiment analysis without NLP API.
        
        Args:
            text: Text to analyze
            
        Returns:
            str: Sentiment category
        """
        text_lower = text.lower()
        
        # Check for emergency keywords first
        if any(keyword in text_lower for keyword in self.emergency_keywords):
            return "emergency"
        
        # Check for negative keywords
        if any(keyword in text_lower for keyword in self.negative_keywords):
            return "negative"
        
        # Check for positive keywords
        if any(keyword in text_lower for keyword in self.positive_keywords):
            return "positive"
        
        return "neutral"
    
    def _get_wellbeing_question(self) -> str:
        """Get a wellbeing question."""
        questions = [
            "How are you feeling right now? Are you comfortable?",
            "Can you tell me if you're experiencing any pain or discomfort?",
            "I want to make sure you're okay. How are you doing today?",
            "Are you feeling well? Please let me know if you need anything."
        ]
        
        self.wellbeing_questions_asked += 1
        return random.choice(questions)
    
    def _get_emergency_response(self) -> str:
        """Get emergency response."""
        return random.choice(self.response_templates['emergency'])
    
    def _get_concern_response(self) -> str:
        """Get concerned response."""
        return random.choice(self.response_templates['concern'])
    
    def _get_reassurance_response(self) -> str:
        """Get reassuring response."""
        return random.choice(self.response_templates['reassurance'])
    
    def _get_clarification_response(self) -> str:
        """Get clarification response."""
        return random.choice(self.response_templates['clarification'])
    
    def _get_greeting(self) -> str:
        """Get greeting message."""
        return random.choice(self.response_templates['greeting'])
    
    def _log_message(self, message: str, sender: str, context: str, tone: str):
        """Log a message to conversation history."""
        chat_message = ChatMessage(
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            message=message,
            sender=sender,
            context=context,
            tone=tone
        )
        
        self.conversation_history.append(chat_message)
        
        # Keep conversation history manageable
        if len(self.conversation_history) > 100:
            self.conversation_history = self.conversation_history[-50:]
    
    def reset_conversation(self):
        """Reset conversation state."""
        self.current_context = "general"
        self.current_tone = "gentle"
        self.wellbeing_questions_asked = 0
        
        # Keep conversation history for context
        print("Conversation reset. Starting fresh context.")
    
    def export_conversation_log(self) -> List[Dict]:
        """
        Export conversation log for analysis.
        
        Returns:
            list: Formatted conversation log
        """
        return [
            {
                "timestamp": msg.timestamp,
                "sender": msg.sender,
                "message": msg.message,
                "context": msg.context,
                "tone": msg.tone
            }
            for msg in self.conversation_history
        ]

# Convenience function for simple usage
def create_senior_chatbot() -> SeniorChatbot:
    """
    Create a senior chatbot instance.
    
    Returns:
        SeniorChatbot: Configured chatbot instance
    """
    return SeniorChatbot()

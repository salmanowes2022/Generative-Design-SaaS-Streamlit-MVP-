"""
Chat Agent Planner
Conversational AI for design generation with brand awareness
Supports multi-turn chat, design iteration, and brand policy enforcement
"""
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
import json
import openai

from app.core.brand_brain import BrandTokens, BrandPolicies
from app.infra.config import settings
from app.infra.logging import get_logger

logger = get_logger(__name__)


@dataclass
class ChatMessage:
    """Single message in conversation"""
    role: str  # 'user', 'assistant', 'system'
    content: str
    timestamp: datetime = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()

    def to_openai_format(self) -> Dict[str, str]:
        """Convert to OpenAI API format"""
        return {"role": self.role, "content": self.content}


@dataclass
class DesignPlan:
    """Structured design plan output"""
    headline: str
    subhead: str
    cta_text: str
    visual_concept: str
    channel: str  # ig, fb, linkedin, twitter
    aspect_ratio: str  # 1x1, 4x5, 9x16, 16x9
    palette_mode: str  # primary, secondary, accent, mono
    background_style: str
    logo_position: str  # TL, TR, BR, BL
    product_image_needed: bool = False
    reasoning: Optional[str] = None  # Why these choices were made

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dict"""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DesignPlan':
        """Create from dict"""
        return cls(**{k: v for k, v in data.items() if k in cls.__annotations__})


class ChatAgentPlanner:
    """
    Conversational design planner with brand awareness

    Features:
    - Multi-turn conversations
    - Brand voice enforcement
    - Forbidden term detection
    - Design iteration support
    - Context-aware suggestions
    """

    def __init__(
        self,
        tokens: BrandTokens,
        policies: BrandPolicies,
        api_key: Optional[str] = None
    ):
        """
        Initialize chat agent

        Args:
            tokens: Brand design tokens
            policies: Brand policies (voice, forbidden terms)
            api_key: OpenAI API key
        """
        # DEBUG: Log what brand data the agent receives
        logger.info(f"🔍 DEBUG - ChatAgent Init")
        # Compatible color access for both BrandTokens and BrandTokensV2
        if hasattr(tokens, 'colors'):
            # BrandTokensV2 format
            primary = tokens.colors.primary.hex
            secondary = tokens.colors.secondary.hex
            accent = tokens.colors.accent.hex
        else:
            # Old BrandTokens format
            primary = tokens.color.get('primary')
            secondary = tokens.color.get('secondary')
            accent = tokens.color.get('accent')
        logger.info(f"🎨 Received Colors: primary={primary}, secondary={secondary}, accent={accent}")
        logger.info(f"📝 Received CTAs: {tokens.cta_whitelist}")
        logger.info(f"🗣️ Received Voice: {policies.voice}")
        logger.info(f"🚫 Received Forbid: {policies.forbid}")

        openai.api_key = api_key or settings.OPENAI_API_KEY
        self.model = "gpt-4-turbo-preview"
        self.tokens = tokens
        self.policies = policies

        # Conversation history
        self.messages: List[ChatMessage] = []

        # System prompt with brand context
        self.system_prompt = self._build_system_prompt()
        logger.info(f"📋 System Prompt Length: {len(self.system_prompt)} chars")
        logger.info(f"📋 System Prompt Preview: {self.system_prompt[:500]}...")

        self.messages.append(ChatMessage(
            role="system",
            content=self.system_prompt
        ))

    def _build_system_prompt(self) -> str:
        """Build system prompt with brand context"""
        voice_traits = ", ".join(self.policies.voice) if self.policies.voice else "Professional, Approachable"
        forbidden = ", ".join(self.policies.forbid) if self.policies.forbid else "None specified"

        available_ctas = ", ".join(self.tokens.cta_whitelist) if self.tokens.cta_whitelist else "Learn More, Get Started"

        # Compatible color access for both BrandTokens and BrandTokensV2
        if hasattr(self.tokens, 'colors'):
            # BrandTokensV2 format
            primary = self.tokens.colors.primary.hex
            secondary = self.tokens.colors.secondary.hex
            accent = self.tokens.colors.accent.hex
        else:
            # Old BrandTokens format
            primary = self.tokens.color.get('primary')
            secondary = self.tokens.color.get('secondary')
            accent = self.tokens.color.get('accent')
        colors_desc = f"Primary: {primary}, Secondary: {secondary}, Accent: {accent}"

        system_prompt = f"""You are an expert brand designer and creative strategist. Your job is to help users create engaging social media designs that perfectly match their brand.

**BRAND CONTEXT:**

**Voice & Personality:**
{voice_traits}

**Forbidden Terms (NEVER use these):**
{forbidden}

**Approved CTAs (ONLY use these):**
{available_ctas}

**Brand Colors:**
{colors_desc}

**Design Constraints:**
- Headlines: Max 7 words
- Subheads: Max 16 words
- Always use CTAs from the approved list
- Visual concepts should be clear, compelling, and brand-aligned
- Avoid clichés and stock photo descriptions

**CRITICAL - Professional Background Images:**
- ALWAYS include PEOPLE or CHARACTERS when appropriate for the campaign
- Use diverse, authentic representations
- Create specific, detailed prompts (not vague descriptions)
- Think like a professional photographer/art director
- Example GOOD: "Close-up of a diverse team of 3 professionals collaborating at a modern workspace, natural lighting, candid expressions, shallow depth of field"
- Example BAD: "Abstract colorful background"
- For product campaigns: Show products in use by real people
- For service campaigns: Show the benefit/outcome with people experiencing it

**Your Role:**
1. Understand the user's campaign goal
2. Ask clarifying questions if needed
3. Generate design plans that match the brand voice
4. Suggest improvements based on brand guidelines
5. Support iteration and refinement

**Output Format:**
When the user asks to create a design, respond with a JSON object in this EXACT format:
{{
  "headline": "Max 7 words here",
  "subhead": "Max 16 words of supporting text",
  "cta_text": "One of the approved CTAs",
  "visual_concept": "Detailed description of the visual (no text, no logos)",
  "channel": "ig|fb|linkedin|twitter",
  "aspect_ratio": "1x1|4x5|9x16|16x9",
  "palette_mode": "primary|secondary|accent|mono",
  "background_style": "Style description for AI image generation",
  "logo_position": "TL|TR|BR|BL",
  "product_image_needed": false,
  "reasoning": "Why you made these choices"
}}

Start each conversation by greeting the user warmly and asking what they'd like to create.
"""
        return system_prompt

    def chat(self, user_message: str) -> str:
        """
        Process user message and return assistant response

        Args:
            user_message: User's input

        Returns:
            Assistant's response
        """
        logger.info(f"User: {user_message[:100]}...")

        # Add user message
        self.messages.append(ChatMessage(role="user", content=user_message))

        # Check for forbidden terms
        violation = self._check_forbidden_terms(user_message)
        if violation:
            warning = f"⚠️ Note: The term '{violation}' goes against brand guidelines. I'll adjust the messaging accordingly."
            logger.warning(warning)

        # Call GPT-4
        try:
            response = openai.chat.completions.create(
                model=self.model,
                messages=[msg.to_openai_format() for msg in self.messages],
                temperature=0.7,
                max_tokens=1500
            )

            assistant_message = response.choices[0].message.content
            logger.info(f"Assistant: {assistant_message[:100]}...")

            # Add to history
            self.messages.append(ChatMessage(
                role="assistant",
                content=assistant_message
            ))

            return assistant_message

        except Exception as e:
            logger.error(f"Chat error: {e}")
            return f"I apologize, I encountered an error: {str(e)}"

    def _check_forbidden_terms(self, text: str) -> Optional[str]:
        """Check if text contains forbidden terms"""
        if not self.policies.forbid:
            return None

        text_lower = text.lower()
        for term in self.policies.forbid:
            if term.lower() in text_lower:
                return term

        return None

    def extract_design_plan(self, assistant_response: str) -> Optional[DesignPlan]:
        """
        Extract DesignPlan from assistant response

        Args:
            assistant_response: Assistant's response containing JSON

        Returns:
            DesignPlan if found, None otherwise
        """
        try:
            # Try to find JSON in response
            json_text = assistant_response

            # Extract from markdown code blocks
            if '```json' in json_text:
                json_text = json_text.split('```json')[1].split('```')[0].strip()
            elif '```' in json_text:
                json_text = json_text.split('```')[1].split('```')[0].strip()

            # Parse JSON
            data = json.loads(json_text)

            # Validate required fields
            required_fields = ['headline', 'subhead', 'cta_text', 'visual_concept']
            if not all(field in data for field in required_fields):
                logger.warning("Missing required fields in design plan")
                return None

            # Validate constraints
            if len(data['headline'].split()) > 7:
                logger.warning(f"Headline too long: {len(data['headline'].split())} words")
                data['headline'] = ' '.join(data['headline'].split()[:7])

            if len(data['subhead'].split()) > 16:
                logger.warning(f"Subhead too long: {len(data['subhead'].split())} words")
                data['subhead'] = ' '.join(data['subhead'].split()[:16])

            # Validate CTA is in whitelist
            if self.tokens.cta_whitelist and data['cta_text'] not in self.tokens.cta_whitelist:
                logger.warning(f"CTA '{data['cta_text']}' not in whitelist, using default")
                data['cta_text'] = self.tokens.cta_whitelist[0] if self.tokens.cta_whitelist else "Learn More"

            # Create plan
            plan = DesignPlan.from_dict(data)
            logger.info(f"Extracted design plan: {plan.headline}")
            return plan

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON from response: {e}")
            return None
        except Exception as e:
            logger.error(f"Failed to extract design plan: {e}")
            return None

    def suggest_improvements(self, current_plan: DesignPlan) -> str:
        """
        Suggest improvements to a design plan

        Args:
            current_plan: Current design plan

        Returns:
            Improvement suggestions
        """
        prompt = f"""I have this design plan:

{json.dumps(current_plan.to_dict(), indent=2)}

Based on the brand guidelines, suggest 2-3 specific improvements.
Consider:
- Brand voice alignment
- Visual impact
- CTA effectiveness
- Platform best practices

Keep suggestions concise and actionable.
"""

        response = self.chat(prompt)
        return response

    def iterate_design(self, current_plan: DesignPlan, feedback: str) -> Optional[DesignPlan]:
        """
        Iterate on a design based on user feedback

        Args:
            current_plan: Current design plan
            feedback: User feedback

        Returns:
            Updated design plan
        """
        prompt = f"""Here's the current design plan:

{json.dumps(current_plan.to_dict(), indent=2)}

User feedback: {feedback}

Please create an updated design plan addressing this feedback.
Return the updated plan in the same JSON format.
"""

        response = self.chat(prompt)
        return self.extract_design_plan(response)

    def get_conversation_history(self) -> List[Dict[str, Any]]:
        """Get conversation history for display"""
        return [
            {
                "role": msg.role,
                "content": msg.content,
                "timestamp": msg.timestamp.isoformat()
            }
            for msg in self.messages
            if msg.role != "system"  # Exclude system prompt
        ]

    def reset_conversation(self):
        """Reset conversation to initial state"""
        self.messages = [ChatMessage(
            role="system",
            content=self.system_prompt
        )]
        logger.info("Conversation reset")

    def export_chat_log(self) -> str:
        """Export conversation as formatted text"""
        log_lines = []
        for msg in self.messages:
            if msg.role != "system":
                timestamp = msg.timestamp.strftime("%Y-%m-%d %H:%M:%S")
                role_label = "You" if msg.role == "user" else "Assistant"
                log_lines.append(f"[{timestamp}] {role_label}:")
                log_lines.append(msg.content)
                log_lines.append("")  # Blank line

        return "\n".join(log_lines)


# Convenience function for single-shot planning
def chat_plan_design(
    user_prompt: str,
    tokens: BrandTokens,
    policies: BrandPolicies
) -> Optional[DesignPlan]:
    """
    Quick function to generate a design plan from a single prompt

    Args:
        user_prompt: User's design request
        tokens: Brand tokens
        policies: Brand policies

    Returns:
        DesignPlan if successful
    """
    agent = ChatAgentPlanner(tokens, policies)
    response = agent.chat(user_prompt)
    return agent.extract_design_plan(response)

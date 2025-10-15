def convert_uuids_to_str(obj):
    """Recursively convert UUIDs and datetimes in dict/list to strings"""
    from uuid import UUID
    from datetime import datetime
    if isinstance(obj, dict):
        return {k: convert_uuids_to_str(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_uuids_to_str(v) for v in obj]
    elif isinstance(obj, UUID):
        return str(obj)
    elif isinstance(obj, datetime):
        return obj.isoformat()
    else:
        return obj
"""
Chat Interface - Natural Language Design Generation

Works with YOUR UUID-based schema
"""

import streamlit as st
import asyncio
from datetime import datetime
from typing import List, Dict
from uuid import UUID

from app.core.design_agent import design_agent
from app.core.brand_memory import brand_memory
from app.core.brandkit import BrandKitManager
from app.infra.db import get_db


# ==================== PAGE CONFIG ====================

st.set_page_config(
    page_title="Chat with Design Agent",
    page_icon="💬",
    layout="wide"
)

st.title("💬 Chat with Your Design Agent")
st.caption("Describe what you need, and I'll design it for you")


# ==================== HELPERS ====================

def get_or_create_conversation(org_id: UUID, user_id: UUID) -> UUID:
    """Get active conversation or create new one"""
    db = get_db()

    # Check for active conversation
    result = db.fetch_one("""
        SELECT id FROM chat_conversations
        WHERE org_id = %s AND user_id = %s AND status = 'active'
        ORDER BY updated_at DESC LIMIT 1
    """, (str(org_id), str(user_id)))

    if result:
        conv_id = result['id']
    else:
        # Create new conversation
        result = db.fetch_one("""
            INSERT INTO chat_conversations (org_id, user_id, title, status)
            VALUES (%s, %s, %s, %s)
            RETURNING id
        """, (str(org_id), str(user_id), "New Design Session", "active"))
        conv_id = result['id']

    return conv_id


def load_conversation_history(conversation_id: UUID) -> List[Dict]:
    """Load all messages from a conversation"""
    db = get_db()

    rows = db.fetch_all("""
        SELECT role, content, design_id, created_at
        FROM chat_messages
        WHERE conversation_id = %s
        ORDER BY created_at ASC
    """, (str(conversation_id),))

    messages = []
    for row in rows:
        messages.append({
            'role': row['role'],
            'content': row['content'],
            'design_id': row['design_id'],
            'timestamp': row['created_at']
        })

    return messages


def save_message(conversation_id: UUID, role: str, content: str, design_id: UUID = None):
    """Save a message to the conversation"""
    db = get_db()

    db.execute("""
        INSERT INTO chat_messages (conversation_id, role, content, design_id, created_at)
        VALUES (%s, %s, %s, %s, %s)
    """, (str(conversation_id), role, content, str(design_id) if design_id else None, datetime.now()))

    # Update conversation timestamp
    db.execute("""
        UPDATE chat_conversations SET updated_at = %s WHERE id = %s
    """, (datetime.now(), str(conversation_id)))


async def process_user_request(
    org_id: UUID,
    user_message: str,
    conversation_history: List[Dict],
    brand_kit_id: UUID
):
    """Process user's design request"""
    
    with st.spinner("🤔 Understanding your request..."):
        # Step 1: Understand intent
        intent = design_agent.understand_request(
            org_id=org_id,
            user_message=user_message,
            conversation_history=conversation_history
        )
        intent = convert_uuids_to_str(intent)
        
        st.success("✅ Got it!")
        
        # Show understanding
        with st.expander("📋 What I understood", expanded=True):
            col1, col2 = st.columns(2)
            with col1:
                st.write("**Design Type:**", intent.get('design_type', 'Not specified'))
                st.write("**Platform:**", intent.get('platform', 'General'))
                st.write("**Aspect Ratio:**", intent.get('aspect_ratio', '1:1'))
            with col2:
                st.write("**Tone:**", intent.get('tone', 'Professional'))
                st.write("**Key Elements:**", ', '.join(intent.get('key_elements', [])) or 'None')
        
    with st.spinner("🎨 Planning the design..."):
        # Step 2: Plan design
        plan = design_agent.plan_design(
            org_id=org_id,
            intent=intent,
            brand_kit_id=brand_kit_id
        )
        
        st.success("✅ Design planned!")
        
        # Show plan
        with st.expander("🧠 My design plan", expanded=True):
            st.write("**Layout:**", plan.get('layout_choice', 'Standard'))
            st.write("**Background Concept:**", plan.get('background_prompt', 'N/A')[:200] + "...")
            
            if plan.get('reasoning'):
                st.info(f"**Why this works:** {plan['reasoning'].get('overall', 'Based on brand guidelines')}")
    
    with st.spinner("✨ Generating your design... (30-60 seconds)"):
        # Step 3: Generate design
        result = design_agent.generate_design(
            org_id=org_id,
            plan=plan
        )
        st.success("🎉 Design complete!")
        return result, plan


# ==================== SESSION STATE ====================

# Get org_id from session or use demo
if 'org_id' not in st.session_state:
    # In production, get this from auth
    db = get_db()
    result = db.fetch_one("SELECT id FROM organizations LIMIT 1")
    st.session_state.org_id = result['id'] if result else None

if 'user_id' not in st.session_state:
    # In production, get this from auth
    db = get_db()
    result = db.fetch_one("SELECT id FROM users WHERE org_id = %s LIMIT 1", (str(st.session_state.org_id),))
    st.session_state.user_id = result['id'] if result else None

if not st.session_state.org_id or not st.session_state.user_id:
    st.error("⚠️ No organization or user found. Please set up your account first.")
    st.stop()

if 'conversation_id' not in st.session_state:
    st.session_state.conversation_id = get_or_create_conversation(
        st.session_state.org_id,
        st.session_state.user_id
    )

if 'messages' not in st.session_state:
    st.session_state.messages = load_conversation_history(st.session_state.conversation_id)


# ==================== SIDEBAR ====================

with st.sidebar:
    st.header("⚙️ Settings")
    
    # Brand kit selector
    brand_kit_manager = BrandKitManager()
    brand_kits = brand_kit_manager.get_brand_kits_by_org(st.session_state.org_id)
    
    if not brand_kits:
        st.warning("⚠️ No brand kits found. Create one first!")
        st.page_link("pages/1_🏁_Onboard_Brand_Kit.py", label="➕ Create Brand Kit")
    else:
        brand_kit_options = {bk.name: bk.id for bk in brand_kits}
        selected_brand_kit = st.selectbox(
            "Brand Kit",
            options=list(brand_kit_options.keys()),
            index=0
        )
        st.session_state.brand_kit_id = brand_kit_options[selected_brand_kit]
    
    st.divider()
    
    # Conversation controls
    st.subheader("💬 Conversation")
    
    if st.button("🔄 New Conversation", use_container_width=True):
        # Archive current conversation
        db = get_db()
        db.execute("""
            UPDATE chat_conversations SET status = 'archived' WHERE id = %s
        """, (str(st.session_state.conversation_id),))

        # Create new
        st.session_state.conversation_id = get_or_create_conversation(
            st.session_state.org_id,
            st.session_state.user_id
        )
        st.session_state.messages = []
        st.rerun()
    
    st.divider()
    
    # Quick tips
    with st.expander("💡 Tips for Better Results"):
        st.markdown("""
        **Be specific about:**
        - Platform (Instagram, Facebook, etc.)
        - Dimensions (1:1, 4:5, 9:16)
        - Tone (friendly, professional, bold)
        - Purpose (launch, promo, announcement)
        
        **Examples:**
        - "Make a 4:5 Instagram post for our summer sale"
        - "Create a professional LinkedIn banner"
        - "Design a bold 9:16 story for product launch"
        """)


# ==================== CHAT DISPLAY ====================

# Display chat history
for msg in st.session_state.messages:
    with st.chat_message(msg['role']):
        st.write(msg['content'])
        
        # If message has a design, show placeholder
        if msg.get('design_id'):
            st.info("🎨 Design generated - view in Library")


# ==================== CHAT INPUT ====================

if not brand_kits:
    st.info("👆 Create a brand kit first to start designing!")
else:
    user_input = st.chat_input("Describe what you need... (e.g., 'Make a 4:5 Instagram post for our sale')")
    
    if user_input:
        # Add user message to chat
        st.session_state.messages.append({
            'role': 'user',
            'content': user_input,
            'timestamp': datetime.now()
        })
        
        save_message(
            st.session_state.conversation_id,
            'user',
            user_input
        )
        
        # Display user message
        with st.chat_message("user"):
            st.write(user_input)
        
        # Process request
        with st.chat_message("assistant"):
            try:
                # Run async process
                result, plan = asyncio.run(process_user_request(
                    org_id=st.session_state.org_id,
                    user_message=user_input,
                    conversation_history=[
                        {'role': m['role'], 'content': m['content']}
                        for m in st.session_state.messages[-6:]
                    ],
                    brand_kit_id=st.session_state.brand_kit_id
                ))
                
                # Show success message
                response_text = f"I created a {plan.get('aspect_ratio')} {plan['intent'].get('design_type')} for {plan['intent'].get('platform')}. Check the Library to view it!"
                
                st.success(response_text)
                # New: Button to go directly to the generated design in Library
                if st.button("Go to Design in Library", key=f"goto_library_{result['asset_id']}"):
                    st.session_state.viewing_asset_id = str(result['asset_id'])
                    st.switch_page("pages/4_Library.py")
                
                # Explanation
                with st.expander("🧠 Why I made these choices"):
                    st.write("**Overall approach:**")
                    st.write(design_agent.explain_decision(plan, 'overall'))
                    
                    st.write("**Layout choice:**")
                    st.write(design_agent.explain_decision(plan, 'layout'))
                
                # Action buttons
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("👍 This works!", key=f"approve_new"):
                        brand_memory.record_feedback(
                            design_id=result['design_id'],
                            org_id=st.session_state.org_id,
                            user_id=st.session_state.user_id,
                            feedback_type='approved',
                            rating=5
                        )
                        st.success("Great! I'll remember what worked.")
                
                with col2:
                    if st.button("🔄 Make it different", key=f"revise_new"):
                        st.info("Tell me what to change in your next message!")
                
                # Save assistant message
                st.session_state.messages.append({
                    'role': 'assistant',
                    'content': response_text,
                    'design_id': str(result['design_id']) if result.get('design_id') else None,
                    'timestamp': datetime.now()
                })
                
                save_message(
                    st.session_state.conversation_id,
                    'assistant',
                    response_text,
                    result['design_id']
                )
                
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
                st.write("Please try rephrasing your request or check your settings.")


# ==================== FOOTER ====================

st.divider()

col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Designs Created", len([m for m in st.session_state.messages if m.get('design_id')]))

with col2:
    context = brand_memory.get_brand_context(st.session_state.org_id, "")
    st.metric("Total Brand Designs", context['stats']['total_designs'])

with col3:
    patterns = brand_memory.get_brand_patterns(st.session_state.org_id)
    st.metric("Learned Patterns", len(patterns))
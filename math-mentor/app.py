




import streamlit as st
from PIL import Image
import os
from dotenv import load_dotenv

# Compatibility fix for Pillow 10.0.0+ where ANTIALIAS was removed
if not hasattr(Image, 'ANTIALIAS'):
    Image.ANTIALIAS = Image.LANCZOS

from utils.ocr import OCRProcessor
from utils.audio import AudioProcessor
from utils.memory import MemorySystem
from utils.hitl import HITLSystem
from agents.parser import ParserAgent
from agents.router import RouterAgent
from agents.solver import SolverAgent
from agents.verifier import VerifierAgent
from agents.explainer import ExplainerAgent
from rag.retriever import Retriever

load_dotenv()

st.set_page_config(page_title="Math Mentor", page_icon="📐", layout="wide")

if 'memory' not in st.session_state:
    st.session_state.memory = MemorySystem()
if 'hitl' not in st.session_state:
    st.session_state.hitl = HITLSystem()
if 'ocr' not in st.session_state:
    st.session_state.ocr = OCRProcessor()
if 'audio' not in st.session_state:
    st.session_state.audio = AudioProcessor()
if 'parser' not in st.session_state:
    st.session_state.parser = ParserAgent()
if 'router' not in st.session_state:
    st.session_state.router = RouterAgent()
if 'solver' not in st.session_state:
    st.session_state.solver = SolverAgent()
if 'verifier' not in st.session_state:
    st.session_state.verifier = VerifierAgent()
if 'explainer' not in st.session_state:
    st.session_state.explainer = ExplainerAgent()
if 'retriever' not in st.session_state:
    st.session_state.retriever = Retriever()

st.title("📐 Math Mentor - AI Problem Solver")
st.markdown("Upload an image, record audio, or type your math problem")

col1, col2 = st.columns([2, 1])

with col1:
    input_mode = st.radio("Input Mode", ["Text", "Image", "Audio"], horizontal=True)
    
    extracted_text = ""
    needs_review = False
    confidence = 1.0
    ocr_confidence = 1.0
    audio_confidence = 1.0
    
    if input_mode == "Text":
        extracted_text = st.text_area("Extracted Text (edit if needed):", value=extracted_text, height=150, key="edited_text")
        
    elif input_mode == "Image":
        uploaded_file = st.file_uploader("Upload image", type=['png', 'jpg', 'jpeg'])
        if uploaded_file:
            image = Image.open(uploaded_file)
            st.image(image, caption="Uploaded Image", use_column_width=True)
            
            with st.spinner("Extracting text from image..."):
                result = st.session_state.ocr.extract_text(image)
                extracted_text = result['text']
                ocr_confidence = result['confidence']
                needs_review = result['needs_review']
            
            col_conf1, col_conf2 = st.columns(2)
            with col_conf1:
                st.metric("OCR Confidence", f"{ocr_confidence:.2%}")
            with col_conf2:
                if needs_review:
                    st.error("⚠️ Low Confidence")
                else:
                    st.success("✅ High Confidence")
            
            extracted_text = st.text_area("Extracted Text (edit if needed):", value=extracted_text, height=150)
            
    elif input_mode == "Audio":
        audio_file = st.file_uploader("Upload audio file", type=['wav', 'mp3', 'm4a'])
        if audio_file:
            st.audio(audio_file)
            
            with st.spinner("Transcribing audio..."):
                result = st.session_state.audio.transcribe(audio_file)
                extracted_text = result['text']
                audio_confidence = result['confidence']
                needs_review = result['needs_review']
            
            col_conf1, col_conf2 = st.columns(2)
            with col_conf1:
                st.metric("Transcription Confidence", f"{audio_confidence:.2%}")
            with col_conf2:
                if needs_review:
                    st.error("⚠️ Low Confidence")
                else:
                    st.success("✅ High Confidence")
            
            extracted_text = st.text_area("Transcription (edit if needed):", value=extracted_text, height=150)
    
    col_btn1, col_btn2 = st.columns(2)
    with col_btn1:
        solve_button = st.button("🚀 Solve Problem", type="primary", disabled=not extracted_text, use_container_width=True)
    with col_btn2:
        recheck_button = st.button("🔍 Request Re-check", disabled=not extracted_text, use_container_width=True)

with col2:
    st.subheader("🔄 Agent Trace")
    trace_container = st.container()

if solve_button and extracted_text:
    final_text = st.session_state.get("edited_text", extracted_text)
    
    # Then use final_text for parsing
    parsed = st.session_state.parser.parse(final_text, input_mode.lower())
    extracted_text = st.session_state.memory.apply_learned_corrections(extracted_text, input_mode.lower())
    
    with trace_container:
        trace = []
        
        st.write("🔍 **Parser Agent**: Analyzing problem...")
        parsed = st.session_state.parser.parse(extracted_text, input_mode.lower())
        trace.append({"agent": "Parser", "output": parsed})
        with st.expander("Parser Output", expanded=False):
            st.json(parsed)
        
        if input_mode == "Image" and extracted_text != result['text']:
            ocr_confidence = 1.0
        if input_mode == "Audio" and extracted_text != result['text']:
            audio_confidence = 1.0

        hitl_check = st.session_state.hitl.should_trigger_hitl(
            ocr_confidence=ocr_confidence,
            audio_confidence=audio_confidence,
            parser_needs_clarification=parsed.get('needs_clarification', False),
            explicit_request=False
        )
        
        if hitl_check['should_trigger']:
            st.error(st.session_state.hitl.get_hitl_instructions(hitl_check))
            st.session_state.hitl_triggered = True
            st.stop()
        
        st.write("🧭 **Router Agent**: Determining strategy...")
        routing = st.session_state.router.route(parsed)
        trace.append({"agent": "Router", "output": routing})
        with st.expander("Router Output", expanded=False):
            st.json(routing)
        
        if routing.get('requires_hitl'):
            st.error(f"❗ HITL Required: {routing.get('reason')}")
            st.info("Please clarify your problem or edit the extracted text.")
            st.stop()
        
        st.write("🔎 **Retriever**: Fetching relevant context...")
        context = st.session_state.retriever.retrieve_context(parsed)
        trace.append({"agent": "Retriever", "sources": len(context['knowledge_base'])})
        st.write(f"📚 Retrieved {len(context['knowledge_base'])} knowledge chunks + {len(context['similar_problems'])} similar problems")
        
        st.write("💡 **Solver Agent**: Solving problem...")
        solution = st.session_state.solver.solve(parsed, context, routing['strategy'])
        trace.append({"agent": "Solver", "steps": len(solution['steps'])})
        if solution.get('calculations_performed', 0) > 0:
            st.write(f"🧮 Performed {solution['calculations_performed']} calculations")
        
        st.write("✅ **Verifier Agent**: Checking solution...")
        verification = st.session_state.verifier.verify(parsed, solution)
        trace.append({"agent": "Verifier", "output": verification})
        
        verifier_hitl = st.session_state.hitl.should_trigger_hitl(
            verifier_confidence=verification.get('confidence', 1.0)
        )
        
        if verifier_hitl['should_trigger']:
            st.warning("⚠️ Verifier has concerns. Solution generated but needs review.")
        
        with st.expander("Verifier Output", expanded=False):
            st.json(verification)
        
        st.write("📚 **Explainer Agent**: Creating explanation...")
        explanation = st.session_state.explainer.explain(parsed, solution, verification)
        
        st.session_state.current_solution = {
            'input_mode': input_mode,
            'original_text': extracted_text,
            'parsed': parsed,
            'routing': routing,
            'solution': solution,
            'verification': verification,
            'explanation': explanation,
            'context': context,
            'trace': trace,
            'hitl_data': verifier_hitl
        }

if recheck_button and extracted_text:
    hitl_explicit = st.session_state.hitl.should_trigger_hitl(explicit_request=True)
    st.warning(st.session_state.hitl.get_hitl_instructions(hitl_explicit))

if 'current_solution' in st.session_state:
    st.markdown("---")
    
    tab1, tab2, tab3, tab4 = st.tabs(["📖 Explanation", "📊 Retrieved Context", "🔍 Solution Details", "📈 Learning Insights"])
    
    with tab1:
        conf = st.session_state.current_solution['verification']['confidence']
        
        col_metric1, col_metric2, col_metric3 = st.columns(3)
        with col_metric1:
            st.metric("Solution Confidence", f"{conf:.2%}")
        with col_metric2:
            is_correct = st.session_state.current_solution['verification']['is_correct']
            st.metric("Verified", "✅ Yes" if is_correct else "⚠️ Review Needed")
        with col_metric3:
            calc_count = st.session_state.current_solution['solution'].get('calculations_performed', 0)
            st.metric("Calculations", calc_count)
        
        if conf < 0.7:
            st.warning("⚠️ Low confidence solution. Please verify carefully.")
        
        st.markdown("### Step-by-Step Explanation")
        st.markdown(st.session_state.current_solution['explanation']['explanation'])
    
    with tab2:
        st.subheader("📚 Knowledge Base Sources")
        for i, item in enumerate(st.session_state.current_solution['context']['knowledge_base'], 1):
            with st.expander(f"Source {i}: {item['metadata']['topic']}"):
                st.write(item['content'])
        
        if st.session_state.current_solution['context']['similar_problems']:
            st.subheader("🔄 Similar Problems from Memory (Self-Learning)")
            for i, prob in enumerate(st.session_state.current_solution['context']['similar_problems'], 1):
                with st.expander(f"Similar Problem {i} (Similarity: {prob.get('similarity', 0):.2%})"):
                    st.write("**Problem:**", prob.get('parsed_question', {}).get('problem_text', ''))
                    if prob.get('user_feedback') == 'correct':
                        st.success("✅ This was a correct solution")
                        if 'solution' in prob:
                            st.write("**Previous Solution:**")
                            st.write(prob['solution'][:300] + "...")
    
    with tab3:
        st.subheader("📝 Full Solution")
        st.write(st.session_state.current_solution['solution']['solution'])
        
        st.subheader("🔍 Verification Results")
        ver = st.session_state.current_solution['verification']
        st.json(ver)
        
        if ver.get('issues'):
            st.subheader("⚠️ Issues Found")
            for issue in ver['issues']:
                st.warning(issue)
    
    with tab4:
        insights = st.session_state.memory.get_learning_insights()
        
        col_i1, col_i2, col_i3 = st.columns(3)
        with col_i1:
            st.metric("Total Problems Solved", insights['total_problems'])
        with col_i2:
            st.metric("Overall Accuracy", f"{insights['accuracy']:.1f}%")
        with col_i3:
            st.metric("Best Strategy", insights['most_successful_strategy'] or "N/A")
        
        if insights['topics_distribution']:
            st.subheader("📊 Topics Distribution")
            st.bar_chart(insights['topics_distribution'])
        
        if insights['common_error_topics']:
            st.subheader("⚠️ Topics Needing Improvement")
            for topic in insights['common_error_topics']:
                st.write(f"- {topic}")
    
    st.markdown("---")
    st.subheader("📝 Provide Feedback (Helps System Learn)")
    
    col_fb1, col_fb2, col_fb3 = st.columns(3)
    
    with col_fb1:
        if st.button("✅ Correct Solution", use_container_width=True):
            st.session_state.memory.store({
                'input_type': st.session_state.current_solution['input_mode'],
                'original_text': st.session_state.current_solution['original_text'],
                'parsed_question': st.session_state.current_solution['parsed'],
                'routing': st.session_state.current_solution['routing'],
                'solution': st.session_state.current_solution['solution']['solution'],
                'verification': st.session_state.current_solution['verification'],
                'user_feedback': 'correct',
                'context_used': st.session_state.current_solution['context']
            })
            st.success("✅ Feedback saved! This solution will help improve future responses.")
            st.balloons()
    
    with col_fb2:
        if st.button("❌ Incorrect Solution", use_container_width=True):
            st.session_state.show_feedback_form = True
    
    with col_fb3:
        if st.button("🔄 Try Again", use_container_width=True):
            del st.session_state.current_solution
            st.rerun()
    
    if st.session_state.get('show_feedback_form'):
        st.markdown("---")
        feedback_comment = st.text_area("What was wrong? Your feedback helps the system learn:", placeholder="e.g., Wrong formula used, calculation error, missed a constraint...")
        
        col_submit, col_cancel = st.columns(2)
        with col_submit:
            if st.button("Submit Feedback", type="primary", use_container_width=True):
                st.session_state.memory.store({
                    'input_type': st.session_state.current_solution['input_mode'],
                    'original_text': st.session_state.current_solution['original_text'],
                    'parsed_question': st.session_state.current_solution['parsed'],
                    'routing': st.session_state.current_solution['routing'],
                    'solution': st.session_state.current_solution['solution']['solution'],
                    'verification': st.session_state.current_solution['verification'],
                    'user_feedback': 'incorrect',
                    'user_comment': feedback_comment,
                    'context_used': st.session_state.current_solution['context']
                })
                st.success("✅ Thank you! This feedback will help the system learn and improve.")
                st.session_state.show_feedback_form = False
                st.rerun()
        
        with col_cancel:
            if st.button("Cancel", use_container_width=True):
                st.session_state.show_feedback_form = False
                st.rerun()

st.sidebar.title("📊 System Statistics")
insights = st.session_state.memory.get_learning_insights()

st.sidebar.metric("Problems Solved", insights['total_problems'])
if insights['total_problems'] > 0:
    st.sidebar.metric("Success Rate", f"{insights['accuracy']:.1f}%")
    
    if insights['most_successful_strategy']:
        st.sidebar.metric("Best Strategy", insights['most_successful_strategy'])
    
    st.sidebar.markdown("### 📚 Topics Learned")
    for topic, count in insights['topics_distribution'].items():
        st.sidebar.write(f"- {topic}: {count}")

st.sidebar.markdown("---")
st.sidebar.info("""
**How This System Learns:**
- Stores all solved problems
- Retrieves similar past solutions
- Learns from your feedback
- Improves OCR/audio corrections
- Identifies successful strategies
""")
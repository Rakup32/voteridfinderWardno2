import streamlit as st

def generate_voter_card(row):
    """Generates a card that only shows up when the user hits Print."""
    
    # CSS to hide everything except the card during printing
    st.markdown("""
        <style>
        @media print {
            body * { visibility: hidden; }
            #voter-card-print, #voter-card-print * { visibility: visible; }
            #voter-card-print { position: absolute; left: 0; top: 0; width: 100%; }
        }
        .voter-card-ui {
            border: 2px solid #c53030;
            padding: 15px;
            border-radius: 10px;
            background: #fff;
            margin-top: 20px;
        }
        </style>
    """, unsafe_allow_html=True)

    # The HTML Card
    card_html = f"""
    <div id="voter-card-print" class="voter-card-ui">
        <h2 style="text-align:center; color:#c53030; margin-top:0;">मतदाता परिचय पत्र</h2>
        <hr>
        <p><b>नाम:</b> {row['मतदाताको नाम']}</p>
        <p><b>मतदाता नं:</b> {row['मतदाता नं']}</p>
        <p><b>उमेर/लिङ्ग:</b> {row['उमेर(वर्ष)']} / {row['लिङ्ग']}</p>
        <p><b>पिता/माता:</b> {row['पिता/माताको नाम']}</p>
        <p><b>पति/पत्नी:</b> {row['पति/पत्नीको नाम']}</p>
    </div>
    """
    st.markdown(card_html, unsafe_allow_html=True)

    # The JavaScript Print Trigger
    st.components.v1.html("""
        <script>
        function doPrint() { window.print(); }
        </script>
        <button onclick="doPrint()" style="width:100%; background:#c53030; color:white; 
        border:none; padding:10px; border-radius:5px; cursor:pointer; font-weight:bold;">
            🖨️ Print This Card
        </button>
    """, height=60)
import streamlit as st
import json
import os
import requests
import random
from datetime import datetime
from twilio.rest import Client

# ==========================================
# SIDEBAR & ADMIN LOGIN (SECURITY LOCK)
# ==========================================
st.sidebar.title("⚙️ Admin Panel")
with st.sidebar.expander("🔐 Staff / Admin Login"):
    admin_pin = st.text_input("Enter PIN to unlock records", type="password")

# Agar PIN 1234 hai, toh saare option khulenge, warna sirf Registration dikhega
is_admin = (admin_pin == "1234") 

if is_admin:
    st.sidebar.success("✅ Admin Access Granted")
    menu = st.sidebar.radio("Main Menu:", ["📝 Register Complaint", "🔍 Search & Update Status", "📊 View All Record"])
else:
    st.sidebar.info("Customer Mode: Sirf complaint darj kar sakte hain.")
    menu = "📝 Register Complaint"


# -----------------------------------------------------
# PAGE 1: REGISTER COMPLAINT (For Customers)
# -----------------------------------------------------
if menu == "📝 Register Complaint":
    st.title("🛠️ Register New Complaint")
    st.markdown("Apni problem yahan darj karein, humara serviceman aapse jaldi contact karega.")
    
    with st.form("complaint_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input("Aapka Naam (Customer Name) *")
            mobile = st.text_input("Aapka WhatsApp Number (10 digits) *")
        with col2:
            address = st.text_input("Pura Address (Full Address) *")
            issue = st.selectbox("Kya Problem Hai? (Select Issue) *", 
                                 ["AC Cooling Issue", "Washing Machine Noise", "Refrigerator Not Working", "RO Water Filter", "Other"])
            
        description = st.text_area("Problem ko detail me batayen (Description)")
        
        # Multiple photo upload (Max 10)
        st.markdown("📸 **Photos (Optional - Max 10)**")
        uploaded_files = st.file_uploader("Kharab product ki photo upload karein", type=['png', 'jpg', 'jpeg'], accept_multiple_files=True)
        
        submit_btn = st.form_submit_button("Submit Complaint")
        
    if submit_btn:
        if not name or not mobile or not address or not issue:
            st.error("Kripya sabhi zaroori (*) fields bharein!")
        else:
            complaint_id = generate_complaint_id()
            public_image_urls = []
            local_file_paths = []
            
            if uploaded_files:
                if len(uploaded_files) > 10:
                    st.warning("Maximum 10 photos ki limit hai. Pehli 10 process ho rahi hain.")
                    uploaded_files = uploaded_files[:10]

                with st.spinner('Photos upload ho rahi hain, kripya pratiksha karein...'):
                    for file in uploaded_files:
                        local_path = os.path.join(UPLOAD_FOLDER, file.name)
                        with open(local_path, "wb") as f:
                            f.write(file.getbuffer())
                        local_file_paths.append(local_path)
                        
                        public_url = upload_image_to_internet(local_path)
                        if public_url:
                            public_image_urls.append(public_url)

            # Data database me save karna
            
            # ⚠️ YAHAN APNE SERVICEMAN KA NUMBER FIX KAR DEIN (Bina +91 ke) ⚠️
            fixed_serviceman_number = "9045447473" # <--- Isey mita kar apna asli number daalein
            
            complaint_data = {
                "id": complaint_id,
                "date": datetime.now().strftime("%d-%m-%Y %I:%M %p"),
                "status": "Pending 🔴",
                "name": name,
                "mobile": mobile,
                "address": address,
                "issue": issue,
                "description": description,
                "local_files": local_file_paths,
                "public_urls": public_image_urls,
                "serviceman_mobile": fixed_serviceman_number
            }
            
            with open(DATA_FILE, 'r+') as f:
                data = json.load(f)
                data.append(complaint_data)
                f.seek(0)
                json.dump(data, f, indent=4)
                
            st.success(f"✅ Complaint Registered! Aapki Complaint ID hai: **{complaint_id}**")

            st.info("System processing messages...")
            
            # ==========================================
            # 1. SERVICEMAN/OWNER KO MESSAGE BHEJNA
            # ==========================================
            serv_msg_body = f"""*New Customer Complaint!* 🚨
*ID:* {complaint_id}
*Name:* {name}
*Mobile:* {mobile}
*Address:* {address}
*Issue:* {issue}
*Details:* {description}"""

            serv_success, serv_response = send_whatsapp_message(
                fixed_serviceman_number, 
                serv_msg_body, 
                public_image_urls
            )

            # ==========================================
            # 2. CUSTOMER KO MESSAGE BHEJNA
            # ==========================================
            cust_msg_body = f"""Hello {name}, 👋

Aapki complaint mil gayi hai. 🛠️
*Complaint ID:* {complaint_id}
*Issue:* {issue}

Humara serviceman jald hi aapse sampark karega. Dhanyawad!"""

            cust_success, cust_response = send_whatsapp_message(mobile, cust_msg_body)

# -----------------------------------------------------
# PAGE 2: SEARCH & UPDATE STATUS
# -----------------------------------------------------
elif menu == "🔍 Search & Update Status":
    st.title("🔍 Search & Manage Complaint")
    st.markdown("Customer ki **Complaint ID** daalkar uski details dekhein, status update karein, ya use delete karein.")
    
    if 'search_result' not in st.session_state:
        st.session_state.search_result = None

    search_id = st.text_input("Enter Complaint ID (e.g., CMP-123456)")
    
    if st.button("Search"):
        if not search_id:
            st.warning("Kripya ID daalein.")
        else:
            with open(DATA_FILE, 'r') as f:
                data = json.load(f)
            
            found = False
            for item in data:
                if item.get('id', '').strip().upper() == search_id.strip().upper():
                    st.session_state.search_result = item
                    found = True
                    break
            
            if not found:
                st.session_state.search_result = None
                st.error(f"❌ '{search_id}' naam ki koi complaint nahi mili!")

    if st.session_state.search_result:
        comp = st.session_state.search_result
        
        st.markdown("---")
        st.subheader("📋 Complaint Details")
        
        col1, col2 = st.columns(2)
        with col1:
            st.write(f"**Complaint ID:** {comp['id']}")
            st.write(f"**Date:** {comp['date']}")
            st.write(f"**Customer Name:** {comp['name']}")
            st.write(f"**Mobile:** {comp['mobile']}")
            st.write(f"**Address:** {comp['address']}")
        with col2:
            st.write(f"**Issue:** {comp['issue']}")
            st.write(f"**Description:** {comp['description']}")
            st.write(f"**Current Status:** {comp['status']}")
            
        st.markdown("### ⚙️ Manage Complaint")
        
        status_options = ["Pending 🔴", "Resolved ✅"]
        current_index = 0 if "Pending" in comp.get('status', 'Pending 🔴') else 1
        
        new_status = st.selectbox("Is complaint ka naya status chunein:", status_options, index=current_index)
        
        # Dono buttons ko aamne-saamne dikhane ke liye columns banaye hain
        col3, col4 = st.columns(2)
        
        with col3:
            if st.button("Update Status & Save"):
                with open(DATA_FILE, 'r') as f:
                    all_data = json.load(f)
                
                for idx, item in enumerate(all_data):
                    if item['id'] == comp['id']:
                        all_data[idx]['status'] = new_status
                        st.session_state.search_result['status'] = new_status 
                        break
                        
                with open(DATA_FILE, 'w') as f:
                    json.dump(all_data, f, indent=4)
                    
                st.success(f"✅ Complaint {comp['id']} ka status update karke **{new_status}** kar diya gaya hai!")

        with col4:
            if st.button("🗑️ Delete Complaint"):
                with open(DATA_FILE, 'r') as f:
                    all_data = json.load(f)
                
                # Naya list banayenge jisme search ki hui ID nahi hogi (yani wo delete ho jayegi)
                updated_data = [item for item in all_data if item['id'] != comp['id']]
                
                with open(DATA_FILE, 'w') as f:
                    json.dump(updated_data, f, indent=4)
                    
                st.session_state.search_result = None
                st.success(f"🗑️ Complaint **{comp['id']}** hamesha ke liye delete ho gayi hai! Page refresh kar lein.")


            # -----------------------------------------------------
# PAGE 3: VIEW ALL RECORDS
# -----------------------------------------------------
elif menu == "📊 View All Record":
    st.title("📊 All Complaints Record")
    st.markdown("Yahan aap saari registered complaints ek sath ek table me dekh sakte hain.")
    
    # JSON file se data read karna
    with open(DATA_FILE, 'r') as f:
        data = json.load(f)
        
    if not data:
        st.info("Abhi tak koi complaint register nahi hui hai.")
    else:
        # Data ko sundar Table/Excel format me dikhana
        st.dataframe(data, use_container_width=True)
        
        
        
        
        st.success(f"✅ Complaint {comp['id']} ka status update karke **{new_status}** kar diya gaya hai!")

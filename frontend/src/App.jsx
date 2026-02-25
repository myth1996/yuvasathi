import { useState, useEffect } from "react"
import "./App.css"

const API = import.meta.env.VITE_API_URL || "http://localhost:8000"

const text = {
  title: {
    bn: "বাংলার যুব সাথী — নথি ফরম্যাটার",
    hi: "बांग्लार युवा साथी — दस्तावेज़ फ़ॉर्मेटर",
    en: "Banglar Yuba Sathi — Document Formatter",
  },
  subtitle: {
    bn: "বাংলার যুব সাথী পোর্টালের জন্য নথি প্রস্তুত করুন",
    hi: "बांग्लार युवा साथी पोर्टल के लिए दस्तावेज़ तैयार करें",
    en: "Prepare your documents for the বাংলার যুব সাথী portal",
  },
  selectDoc: { bn: "নথির ধরন বেছে নিন", hi: "दस्तावेज़ प्रकार चुनें", en: "Select document type" },
  convert: { bn: "রূপান্তর করুন", hi: "कन्वर्ट करें", en: "Convert & Compress" },
  converting: { bn: "হচ্ছে...", hi: "हो रहा है...", en: "Converting..." },
  success: { bn: "সফল! ✅", hi: "सफल! ✅", en: "Success! ✅" },
  download: { bn: "ডাউনলোড করুন", hi: "डाउनलोड करें", en: "Download" },
  freeUsed: { bn: "বিনামূল্যে রূপান্তর শেষ!", hi: "मुफ्त कन्वर्शन खत्म!", en: "Free conversions used up!" },
  choosePlan: { bn: "একটি প্ল্যান বেছে নিন", hi: "एक प्लान चुनें", en: "Choose a plan to continue" },
  tipsTitle: {
    bn: "পোর্টালে জমা দেওয়ার আগে মনে রাখুন",
    hi: "पोर्टल पर जमा करने से पहले याद रखें",
    en: "Before submitting to the portal",
  },
  tip1: {
    bn: "📱 আপনার মোবাইল নম্বর প্রস্তুত রাখুন — পোর্টাল OTP পাঠাবে",
    hi: "📱 अपना मोबाइल नंबर तैयार रखें — पोर्टल OTP भेजेगा",
    en: "📱 Keep your mobile number ready — the portal will send an OTP",
  },
  tip2: {
    bn: "✍️ সমস্ত PDF নথি জমা দেওয়ার আগে স্বপ্রত্যয়িত করুন",
    hi: "✍️ सभी PDF दस्तावेज़ जमा करने से पहले स्व-सत्यापित करें",
    en: "✍️ All PDF documents must be Self Attested before uploading",
  },
  tip3: {
    bn: "🖼️ ছবি ও স্বাক্ষর JPG বা PNG ফরম্যাটে হতে হবে",
    hi: "🖼️ फोटो और हस्ताक्षर JPG या PNG फॉर्मेट में होने चाहिए",
    en: "🖼️ Photo and Signature must be JPG or PNG format",
  },
  uploadNote: {
    bn: "ফাইল আপলোড করুন — আমরা স্বয়ংক্রিয়ভাবে সঠিক সাইজে রূপান্তর করব",
    hi: "फ़ाइल अपলोड करें — हम स्वचालित रूप से सही आकार में बदल देंगे",
    en: "Upload your file — we'll compress it to the required size automatically",
  },
}

const documents = [
  {
    id: "pdf1",
    label: {
      bn: "মাধ্যমিক অ্যাডমিট কার্ড (স্বপ্রত্যয়িত)",
      hi: "माध्यमिक एडमिट कार्ड (स्व-सत्यापित)",
      en: "Madhyamik Admit Card (Self Attested)",
    },
    type: "pdf",
    format: "PDF only",
    maxSize: "max 300 KB",
  },
  {
    id: "pdf2",
    label: {
      bn: "মার্কশিট / শিক্ষাগত সার্টিফিকেট (স্বপ্রত্যয়িত)",
      hi: "मार्कशीट / शैक्षणिक प्रमाण पत्र (स्व-सत्यापित)",
      en: "Marksheet / Educational Certificate (Self Attested)",
    },
    type: "pdf",
    format: "PDF only",
    maxSize: "max 300 KB",
  },
  {
    id: "pdf3",
    label: {
      bn: "আধার কার্ডের কপি (স্বপ্রত্যয়িত)",
      hi: "आधार कार्ड की कॉपी (स्व-सत्यापित)",
      en: "Aadhaar Card Copy (Self Attested)",
    },
    type: "pdf",
    format: "PDF only",
    maxSize: "max 300 KB",
  },
  {
    id: "pdf4",
    label: {
      bn: "ভোটার কার্ডের কপি (স্বপ্রত্যয়িত)",
      hi: "वोटर कार्ड की कॉपी (स्व-सत्यापित)",
      en: "Voter Card Copy (Self Attested)",
    },
    type: "pdf",
    format: "PDF only",
    maxSize: "max 300 KB",
  },
  {
    id: "pdf5",
    label: {
      bn: "পাসবুকের প্রথম পাতা (স্বপ্রত্যয়িত)",
      hi: "पासबुक का पहला पेज (स्व-सत्यापित)",
      en: "Bank Passbook First Page (Self Attested)",
    },
    type: "pdf",
    format: "PDF only",
    maxSize: "max 300 KB",
  },
  {
    id: "pdf6",
    label: {
      bn: "SC/ST/OBC সার্টিফিকেট (স্বপ্রত্যয়িত)",
      hi: "SC/ST/OBC प्रमाण पत्र (स्व-सत्यापित)",
      en: "SC/ST/OBC Certificate (Self Attested)",
    },
    type: "pdf",
    format: "PDF only",
    maxSize: "max 300 KB",
  },
  {
    id: "photo",
    label: {
      bn: "পাসপোর্ট সাইজের ছবি",
      hi: "पासपोर्ट साइज़ फोटो",
      en: "Passport Size Photo",
    },
    type: "photo",
    format: "JPG or PNG",
    maxSize: "max 50 KB",
  },
  {
    id: "sig",
    label: {
      bn: "আবেদনকারীর স্বাক্ষর",
      hi: "आवेदक के हस्ताक्षर",
      en: "Applicant Signature",
    },
    type: "signature",
    format: "JPG or PNG",
    maxSize: "max 50 KB",
  },
]

export default function App() {
  const [lang, setLang] = useState("en")
  const [selectedDoc, setSelectedDoc] = useState(null)
  const [file, setFile] = useState(null)
  const [status, setStatus] = useState("idle")
  const [downloadUrl, setDownloadUrl] = useState(null)
  const [freeUsed, setFreeUsed] = useState(0)
  const [docsAllowed, setDocsAllowed] = useState(0)
  const [accessToken, setAccessToken] = useState(null)
  const [showPaywall, setShowPaywall] = useState(false)
  const [serverRemaining, setServerRemaining] = useState(2)
  const [cashfree, setCashfree] = useState(null)

  const t = (key) => text[key][lang]
  const isFree = serverRemaining > 0
  const hasPaid = docsAllowed > 0
  const isPdf = selectedDoc?.type === "pdf"

  useEffect(() => {
    const script = document.createElement("script")
    script.src = "https://sdk.cashfree.com/js/v3/cashfree.js"
    script.async = true
    script.onload = () => {
      const cf = window.Cashfree({ mode: import.meta.env.VITE_CASHFREE_MODE || "production" })
      setCashfree(cf)
    }
    document.body.appendChild(script)
    return () => document.body.removeChild(script)
  }, [])

  useEffect(() => {
    fetch(`${API}/check-limit`)
      .then(r => r.json())
      .then(d => setServerRemaining(d.remaining))
      .catch(() => {})
  }, [freeUsed])

  async function handleConvert() {
    if (!file || !selectedDoc) return
    if (!isFree && !hasPaid) { setShowPaywall(true); return }
    setStatus("converting")
    setDownloadUrl(null)
    const endpoint = selectedDoc.type === "pdf"
      ? `${API}/convert/pdf`
      : selectedDoc.type === "photo"
      ? `${API}/convert/photo`
      : `${API}/convert/signature`
    try {
      const headers = {}
      if (hasPaid && accessToken) headers["Authorization"] = `Bearer ${accessToken}`
      const formData = new FormData()
      formData.append("file", file)
      const res = await fetch(endpoint, { method: "POST", body: formData, headers })
      if (res.status === 402) { setShowPaywall(true); setStatus("idle"); return }
      const blob = await res.blob()
      setDownloadUrl(URL.createObjectURL(blob))
      setStatus("done")
      if (hasPaid) setDocsAllowed(prev => prev - 1)
      else setFreeUsed(prev => prev + 1)
    } catch (e) {
      setStatus("error")
    }
  }

  async function handlePayment(plan) {
    try {
      const res = await fetch(`${API}/payment/create-order?plan=${plan}`, { method: "POST" })
      const order = await res.json()
      if (!cashfree) { alert("Payment loading, please try again."); return }
      cashfree.checkout({
        paymentSessionId: order.payment_session_id,
        redirectTarget: "_modal"
      }).then(async function(result) {
        if (result.paymentDetails) {
          const verify = await fetch(`${API}/payment/verify`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ order_id: order.order_id, plan })
          })
          const data = await verify.json()
          if (data.success && data.token) {
            setAccessToken(data.token)
            setDocsAllowed(plan === "student" ? 6 : 50)
            setShowPaywall(false)
          }
        }
      })
    } catch(e) {
      alert("Payment failed. Please try again.")
    }
  }

  return (
    <div className="app-root">

      {/* Header */}
      <div className="app-header">
        <h1 className="app-title">{t("title")}</h1>
        <p className="app-subtitle">{t("subtitle")}</p>
        <div className="lang-row">
          {["en", "bn", "hi"].map(l => (
            <button
              key={l}
              onClick={() => setLang(l)}
              className={`lang-btn${lang === l ? " lang-btn-active" : ""}`}
            >
              {l === "en" ? "English" : l === "bn" ? "বাংলা" : "हिंदी"}
            </button>
          ))}
        </div>
        <div className="usage-bar">
          {isFree
            ? `✨ ${serverRemaining} free conversion${serverRemaining !== 1 ? "s" : ""} left`
            : hasPaid
            ? `📄 ${docsAllowed} doc${docsAllowed !== 1 ? "s" : ""} remaining`
            : `⚠️ ${t("freeUsed")}`}
        </div>
      </div>

      {/* Main content */}
      <div className="app-content">

        {/* Paywall modal */}
        {showPaywall && (
          <div className="paywall-backdrop">
            <div className="paywall-modal">
              <h2 style={{ marginBottom: "8px" }}>🔒 {t("freeUsed")}</h2>
              <p style={{ color: "#6b7280", marginBottom: "24px", fontSize: "0.9rem" }}>{t("choosePlan")}</p>
              <div onClick={() => handlePayment("student")} className="plan-card plan-card-blue">
                <div className="plan-price blue">₹15</div>
                <div className="plan-name">🧑‍🎓 Student Pack</div>
                <div className="plan-desc">Next 6 documents — perfect for Yuva Sathi!</div>
              </div>
              <div onClick={() => handlePayment("cafe")} className="plan-card plan-card-purple">
                <div className="plan-price purple">₹49</div>
                <div className="plan-name">🖥️ Cyber Café Pack</div>
                <div className="plan-desc">50 documents · 24 hours</div>
              </div>
              <div className="secured-note">🔒 Secured by Cashfree · We never store your documents</div>
              <button onClick={() => setShowPaywall(false)} className="cancel-btn">Cancel</button>
            </div>
          </div>
        )}

        {/* Portal tips */}
        <div className="tips-box">
          <div className="tips-title">{t("tipsTitle")}</div>
          <div className="tip-item">{t("tip1")}</div>
          <div className="tip-item">{t("tip2")}</div>
          <div className="tip-item">{t("tip3")}</div>
        </div>

        {/* Document selector */}
        <p className="section-label">{t("selectDoc")}</p>
        <div className="doc-grid">
          {documents.map(doc => {
            const isSelected = selectedDoc?.id === doc.id
            return (
              <div
                key={doc.id}
                onClick={() => {
                  setSelectedDoc(doc)
                  setFile(null)
                  setStatus("idle")
                  setDownloadUrl(null)
                }}
                className={`doc-card${isSelected ? " doc-card-selected" : ""}`}
              >
                <div className="doc-label">{doc.label[lang]}</div>
                <div className={`doc-badge${isSelected ? " doc-badge-selected" : ""}`}>
                  {doc.type === "pdf" ? "📄" : "🖼️"} {doc.format} · {doc.maxSize}
                </div>
              </div>
            )
          })}
        </div>

        {/* File upload */}
        {selectedDoc && (
          <div className="upload-box">
            <p className="upload-note">{t("uploadNote")}</p>
            <input
              type="file"
              accept={isPdf ? "application/pdf" : "image/jpeg,image/png"}
              onChange={e => {
                setFile(e.target.files[0])
                setStatus("idle")
                setDownloadUrl(null)
              }}
              className="file-input"
            />
            {file && (
              <p className="file-info">
                📄 {file.name} ({(file.size / 1024).toFixed(1)} KB)
                {file.size / 1024 > (isPdf ? 300 : 50) && (
                  <span className="size-warning"> · will be compressed to {isPdf ? "300 KB" : "50 KB"}</span>
                )}
              </p>
            )}
            <button
              onClick={handleConvert}
              disabled={!file || status === "converting"}
              className="convert-btn"
            >
              {status === "converting" ? t("converting") : t("convert")}
            </button>
          </div>
        )}

        {/* Success */}
        {status === "done" && downloadUrl && (
          <div className="success-box">
            <p className="success-text">{t("success")}</p>
            <p className="success-sub">
              {isPdf ? "✅ PDF compressed to ≤ 300 KB" : "✅ Image compressed to ≤ 50 KB"} — ready to upload to the portal
            </p>
            <a href={downloadUrl} download="converted_file" className="download-btn">
              ⬇️ {t("download")}
            </a>
          </div>
        )}

        {status === "error" && (
          <p style={{ color: "red", textAlign: "center" }}>Something went wrong. Please try again.</p>
        )}

        <div className="footer-note">
          🔒 We never store your documents · Deleted immediately after conversion
        </div>
      </div>
    </div>
  )
}

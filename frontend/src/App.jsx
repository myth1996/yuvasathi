import { useState, useEffect } from "react"

const text = {
  title: { bn: "যুব সাথী নথি ফরম্যাটার", hi: "युवा साथी दस्तावेज़ फ़ॉर्मेटर", en: "Yuva Sathi Document Formatter" },
  subtitle: { bn: "যেকোনো সাইজের ফাইল আপলোড করুন", hi: "कोई भी फ़ाइल अपलोड करें", en: "Upload any file — we'll format it for the portal" },
  selectDoc: { bn: "নথির ধরন বেছে নিন", hi: "दस्तावेज़ प्रकार चुनें", en: "Select document type" },
  convert: { bn: "রূপান্তর করুন", hi: "कन्वर्ट करें", en: "Convert" },
  converting: { bn: "হচ্ছে...", hi: "हो रहा है...", en: "Converting..." },
  success: { bn: "সফল! ✅", hi: "सफल! ✅", en: "Success! ✅" },
  download: { bn: "ডাউনলোড করুন", hi: "डाउनलोड करें", en: "Download" },
  freeUsed: { bn: "বিনামূল্যে রূপান্তর শেষ!", hi: "मुफ्त कन्वर्शन खत्म!", en: "Free conversions used up!" },
  choosePlan: { bn: "একটি প্ল্যান বেছে নিন", hi: "एक प्लान चुनें", en: "Choose a plan to continue" },
}

const documents = [
  { id: "pdf1", label: { bn: "মাধ্যমিক অ্যাডমিট কার্ড", hi: "एडमिट कार्ड", en: "Madhyamik Admit Card" }, type: "pdf" },
  { id: "pdf2", label: { bn: "মার্কশিট", hi: "मार्कशीट", en: "Marksheet" }, type: "pdf" },
  { id: "pdf3", label: { bn: "আধার কার্ড", hi: "आधार कार्ड", en: "Aadhaar Card" }, type: "pdf" },
  { id: "pdf4", label: { bn: "ভোটার কার্ড", hi: "वोटर कार्ड", en: "Voter Card" }, type: "pdf" },
  { id: "pdf5", label: { bn: "ব্যাংক পাসবুক", hi: "बैंक पासबुक", en: "Bank Passbook" }, type: "pdf" },
  { id: "pdf6", label: { bn: "জাতি শংসাপত্র", hi: "जाति प्रमाण पत्र", en: "Caste Certificate" }, type: "pdf" },
  { id: "photo", label: { bn: "পাসপোর্ট ছবি", hi: "पासपोर्ट फोटो", en: "Passport Photo" }, type: "photo" },
  { id: "sig", label: { bn: "স্বাক্ষর", hi: "हस्ताक्षर", en: "Signature" }, type: "signature" },
]

export default function App() {
  const [lang, setLang] = useState("en")
  const [selectedDoc, setSelectedDoc] = useState(null)
  const [file, setFile] = useState(null)
  const [status, setStatus] = useState("idle")
  const [downloadUrl, setDownloadUrl] = useState(null)
  const [freeUsed, setFreeUsed] = useState(0)
  const [docsAllowed, setDocsAllowed] = useState(0)
  const [showPaywall, setShowPaywall] = useState(false)
  const [serverRemaining, setServerRemaining] = useState(2)
  const [cashfree, setCashfree] = useState(null)

  const t = (key) => text[key][lang]
  const isFree = serverRemaining > 0
  const hasPaid = docsAllowed > 0

  useEffect(() => {
    const script = document.createElement("script")
    script.src = "https://sdk.cashfree.com/js/v3/cashfree.js"
    script.async = true
    script.onload = () => {
      const cf = window.Cashfree({ mode: "sandbox" })
      setCashfree(cf)
    }
    document.body.appendChild(script)
    return () => document.body.removeChild(script)
  }, [])

  useEffect(() => {
    fetch("http://127.0.0.1:8000/check-limit")
      .then(r => r.json())
      .then(d => setServerRemaining(d.remaining))
  }, [freeUsed])

  async function handleConvert() {
    if (!file || !selectedDoc) return
    if (!isFree && !hasPaid) { setShowPaywall(true); return }
    setStatus("converting")
    setDownloadUrl(null)

    const endpoint = selectedDoc.type === "pdf"
      ? "http://127.0.0.1:8000/convert/pdf"
      : selectedDoc.type === "photo"
      ? "http://127.0.0.1:8000/convert/photo"
      : "http://127.0.0.1:8000/convert/signature"

    try {
      const headers = {}
      if (hasPaid) headers["X-Access-Token"] = "paid"
      const formData = new FormData()
      formData.append("file", file)
      const res = await fetch(endpoint, { method: "POST", body: formData, headers })
      if (res.status === 402) {
        setShowPaywall(true)
        setStatus("idle")
        return
      }
      const blob = await res.blob()
      setDownloadUrl(URL.createObjectURL(blob))
      setStatus("done")
      setFreeUsed(prev => prev + 1)
    } catch (e) {
      setStatus("error")
    }
  }

  async function handlePayment(plan) {
    try {
      const res = await fetch(`http://127.0.0.1:8000/payment/create-order?plan=${plan}`, { method: "POST" })
      const order = await res.json()

      if (!cashfree) { alert("Payment loading, please try again."); return }

      cashfree.checkout({
        paymentSessionId: order.payment_session_id,
        redirectTarget: "_modal"
      }).then(async function(result) {
        if (result.paymentDetails) {
          const verify = await fetch("http://127.0.0.1:8000/payment/verify", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ order_id: order.order_id, plan })
          })
          const data = await verify.json()
          if (data.success) {
            setDocsAllowed(data.docs_allowed)
            setShowPaywall(false)
          }
        }
      })
    } catch(e) {
      alert("Payment failed. Please try again.")
    }
  }

  return (
    <div style={{ minHeight: "100vh", background: "#f0f4ff", fontFamily: "sans-serif" }}>

      <div style={{ background: "linear-gradient(135deg, #2563eb, #7c3aed)", padding: "24px", textAlign: "center" }}>
        <h1 style={{ color: "white", fontSize: "1.5rem", marginBottom: "8px" }}>{t("title")}</h1>
        <p style={{ color: "rgba(255,255,255,0.85)", fontSize: "0.9rem" }}>{t("subtitle")}</p>
        <div style={{ marginTop: "12px", display: "flex", justifyContent: "center", gap: "8px" }}>
          {["en", "bn", "hi"].map(l => (
            <button key={l} onClick={() => setLang(l)} style={{
              padding: "4px 14px", borderRadius: "20px", border: "none", cursor: "pointer",
              background: lang === l ? "white" : "rgba(255,255,255,0.2)",
              color: lang === l ? "#2563eb" : "white", fontWeight: "bold"
            }}>
              {l === "en" ? "English" : l === "bn" ? "বাংলা" : "हिंदी"}
            </button>
          ))}
        </div>
        <div style={{ marginTop: "10px", color: "rgba(255,255,255,0.9)", fontSize: "0.85rem" }}>
          {isFree ? `✨ ${serverRemaining} free conversions left` : hasPaid ? `📄 ${docsAllowed} docs remaining` : `⚠️ ${t("freeUsed")}`}
        </div>
      </div>

      <div style={{ maxWidth: "600px", margin: "0 auto", padding: "24px" }}>

        {showPaywall && (
          <div style={{ position: "fixed", top: 0, left: 0, right: 0, bottom: 0, background: "rgba(0,0,0,0.6)", display: "flex", alignItems: "center", justifyContent: "center", zIndex: 999 }}>
            <div style={{ background: "white", borderRadius: "16px", padding: "32px", maxWidth: "400px", width: "90%", textAlign: "center" }}>
              <h2 style={{ marginBottom: "8px" }}>🔒 {t("freeUsed")}</h2>
              <p style={{ color: "#6b7280", marginBottom: "24px", fontSize: "0.9rem" }}>{t("choosePlan")}</p>
              <div onClick={() => handlePayment("student")} style={{ border: "2px solid #2563eb", borderRadius: "12px", padding: "16px", marginBottom: "12px", cursor: "pointer", background: "#f0f4ff" }}>
                <div style={{ fontSize: "1.8rem", fontWeight: "bold", color: "#2563eb" }}>₹15</div>
                <div style={{ fontWeight: "bold", margin: "4px 0" }}>🧑‍🎓 Student Pack</div>
                <div style={{ fontSize: "0.82rem", color: "#6b7280" }}>Next 6 documents — perfect for Yuva Sathi!</div>
              </div>
              <div onClick={() => handlePayment("cafe")} style={{ border: "2px solid #7c3aed", borderRadius: "12px", padding: "16px", marginBottom: "16px", cursor: "pointer", background: "#f5f3ff" }}>
                <div style={{ fontSize: "1.8rem", fontWeight: "bold", color: "#7c3aed" }}>₹49</div>
                <div style={{ fontWeight: "bold", margin: "4px 0" }}>🖥️ Cyber Café Pack</div>
                <div style={{ fontSize: "0.82rem", color: "#6b7280" }}>50 documents · 24 hours</div>
              </div>
              <div style={{ fontSize: "0.75rem", color: "#9ca3af", marginBottom: "12px" }}>🔒 Secured by Cashfree · We never store your documents</div>
              <button onClick={() => setShowPaywall(false)} style={{ background: "none", border: "none", color: "#9ca3af", cursor: "pointer" }}>Cancel</button>
            </div>
          </div>
        )}

        <p style={{ fontWeight: "bold", marginBottom: "12px" }}>{t("selectDoc")}</p>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "10px", marginBottom: "24px" }}>
          {documents.map(doc => (
            <div key={doc.id} onClick={() => setSelectedDoc(doc)} style={{
              padding: "12px", borderRadius: "10px", cursor: "pointer", fontSize: "0.85rem",
              background: selectedDoc?.id === doc.id ? "#2563eb" : "white",
              color: selectedDoc?.id === doc.id ? "white" : "#1a1a2e",
              border: `2px solid ${selectedDoc?.id === doc.id ? "#2563eb" : "#e5e7eb"}`,
              textAlign: "center"
            }}>
              {doc.label[lang]}
            </div>
          ))}
        </div>

        {selectedDoc && (
          <div style={{ background: "white", borderRadius: "12px", padding: "20px", marginBottom: "16px", textAlign: "center" }}>
            <input type="file" onChange={e => setFile(e.target.files[0])} style={{ marginBottom: "12px" }} />
            {file && <p style={{ fontSize: "0.8rem", color: "#6b7280", marginBottom: "12px" }}>📄 {file.name} ({(file.size / 1024).toFixed(1)} KB)</p>}
            <button onClick={handleConvert} disabled={!file || status === "converting"} style={{
              background: "#2563eb", color: "white", border: "none", borderRadius: "8px",
              padding: "12px 32px", fontSize: "1rem", cursor: "pointer", width: "100%"
            }}>
              {status === "converting" ? t("converting") : t("convert")}
            </button>
          </div>
        )}

        {status === "done" && downloadUrl && (
          <div style={{ background: "#d1fae5", borderRadius: "12px", padding: "20px", textAlign: "center" }}>
            <p style={{ color: "#065f46", fontWeight: "bold", marginBottom: "12px" }}>{t("success")}</p>
            <a href={downloadUrl} download="converted_file" style={{
              background: "#10b981", color: "white", borderRadius: "8px",
              padding: "12px 32px", textDecoration: "none", fontWeight: "bold"
            }}>⬇️ {t("download")}</a>
          </div>
        )}

        {status === "error" && <p style={{ color: "red", textAlign: "center" }}>Something went wrong. Please try again.</p>}

        <div style={{ textAlign: "center", marginTop: "20px", fontSize: "0.75rem", color: "#9ca3af" }}>
          🔒 We never store your documents · Deleted immediately after conversion
        </div>
      </div>
    </div>
  )
}

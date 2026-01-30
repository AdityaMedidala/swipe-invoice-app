# Swipe Invoice Management System

> AI-Powered Invoice Data Extraction and Management System

## 📋 Overview

An intelligent invoice management system that automates the extraction, processing, and management of invoice data from various file formats using AI. Built for Swipe's internship assignment.

**[Live Demo](YOUR_DEPLOYMENT_LINK)** | **[Documentation](./docs)**

## ✨ Features

### Core Functionality
- 🤖 **AI-Powered Extraction**: Uses Google Document AI + Gemini LLM
- 📄 **Multi-Format Support**: PDF, Images (JPG, PNG), Excel, CSV
- 📊 **Three-Tab Dashboard**: Invoices, Products, Customers
- 🔄 **Real-Time Sync**: Redux-powered cross-tab updates
- ✅ **Smart Validation**: Missing field detection and consistency checks
- 📦 **Batch Processing**: Upload multiple files simultaneously

### Advanced Features
- 💰 Tax-aware calculations with automatic totals
- 🏦 Bank detail extraction
- 📝 Amount in words conversion
- 📈 Customer purchase history tracking
- 🔢 Product quantity aggregation
- ✏️ Inline editing with cascade updates
- 🎨 Status indicators (OK, Incomplete, Mismatch)

## 🏗️ Architecture

```
┌─────────────┐         ┌──────────────┐
│   React     │────────▶│   FastAPI    │
│  Frontend   │         │   Backend    │
│  (TypeScript)│◀────────│  (Python)    │
└─────────────┘         └──────────────┘
      │                        │
      │                        ├─────▶ Google Document AI
      │                        │
      ├─ Redux Store           ├─────▶ Google Gemini LLM
      │                        │
      ├─ Mantine UI            └─────▶ Pandas (Excel)
      │
      └─ React Dropzone
```

## 🚀 Tech Stack

### Frontend
- **Framework**: React 18 with TypeScript
- **State Management**: Redux Toolkit
- **UI Library**: Mantine UI v7
- **Tables**: Mantine React Table
- **File Upload**: React Dropzone

### Backend
- **Framework**: FastAPI (Python 3.12)
- **OCR**: Google Document AI
- **LLM**: Google Gemini 2.5 Flash
- **Data Processing**: Pandas
- **Server**: Uvicorn

## 📦 Installation

### Prerequisites
- Node.js 18+
- Python 3.12+
- Google Cloud account with Document AI enabled
- Gemini API key

### Frontend Setup

```bash
# Clone repository
git clone https://github.com/YOUR_USERNAME/swipe-invoice-system.git
cd swipe-invoice-system/frontend

# Install dependencies
npm install

# Start development server
npm start
```

### Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env and add your API keys

# Add Google Cloud credentials
# Place service-account-key.json in backend directory

# Start server
python main.py
```

The backend will run on `http://localhost:8000`  
The frontend will run on `http://localhost:3000`

## 🔑 Configuration

### Backend `.env` file:
```env
GEMINI_API_KEY=your_gemini_api_key_here
PROJECT_ID=your_google_cloud_project_id
LOCATION=us
PROCESSOR_ID=your_document_ai_processor_id
```

### Google Cloud Setup:
1. Create a Google Cloud project
2. Enable Document AI API
3. Create a Document AI processor (Invoice Parser)
4. Create a service account and download JSON key
5. Save as `service-account-key.json` in backend directory

### Gemini API:
1. Get API key from [Google AI Studio](https://aistudio.google.com/app/apikey)
2. Add to `.env` file

## 📖 Usage

### 1. Upload Files
- Drag and drop files onto the upload area
- Or click to browse and select files
- Supports: PDF, JPG, PNG, XLSX, XLS, CSV

### 2. View Extracted Data
- **Invoices Tab**: View all invoices with details
- **Products Tab**: See aggregated product data
- **Customers Tab**: Track customer purchase history

### 3. Edit Data
- Click the edit icon (pencil) in any table
- Make changes inline
- Changes automatically sync across all tabs

### 4. Validate Data
- Red text indicates missing required fields
- Status badges show data completeness
- Expand invoice rows for detailed breakdown

## 🧪 Test Cases

All test cases from the assignment have been successfully implemented:

| Test Case | Description | Status |
|-----------|-------------|--------|
| Case 1 | Invoice PDFs | ✅ Passed |
| Case 2 | PDF + Images | ✅ Passed |
| Case 3 | Single Excel File | ✅ Passed |
| Case 4 | Multiple Excel Files | ✅ Passed |
| Case 5 | All File Types | ✅ Passed |

See [test documentation](./docs/test-cases.md) for detailed results with screenshots.

## 📁 Project Structure

```
swipe-invoice-system/
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── Dashboard.tsx
│   │   │   └── UploadArea.tsx
│   │   ├── features/
│   │   │   └── data/
│   │   │       └── dataSlice.ts
│   │   ├── store/
│   │   │   └── store.ts
│   │   └── types/
│   │       └── types.ts
│   └── package.json
│
├── backend/
│   ├── main.py          # FastAPI application
│   ├── docai.py         # Document AI integration
│   ├── llm.py           # Gemini LLM extraction
│   ├── validator.py     # Data validation
│   └── requirements.txt
│
└── README.md
```

## 🔄 Data Flow

1. **Upload** → User drops files in upload area
2. **Route** → Backend routes files by type (PDF/Image → DocAI, Excel → Pandas)
3. **Extract** → AI extracts structured data using Gemini prompts
4. **Validate** → Validator checks completeness and consistency
5. **Store** → Redux dispatches action to update state
6. **Sync** → All tabs automatically update with new data
7. **Edit** → User can edit data with cascade updates across tabs

## 🎯 Key Algorithms

### Product Aggregation
```typescript
// Products are matched by name across invoices
// Quantities are summed, prices updated if newer data available
if (existing) {
  existing.quantity += item.quantity;
  if (price > 0) existing.unitPrice = price;
}
```

### Customer Tracking
```typescript
// Customer totals calculated by summing all their invoices
cust.totalPurchaseAmount = invoices
  .filter(inv => inv.customerName === cust.name)
  .reduce((sum, inv) => sum + inv.totalAmount, 0);
```

### Consistency Validation
```typescript
// Invoice is consistent if calculated total matches stated total
const calculated = items.reduce((sum, i) => sum + i.amount, 0) + taxTotal;
const variance = Math.abs(statedTotal - calculated);
isConsistent = variance < 1.0;
```

## 🐛 Known Limitations

- OCR accuracy depends on image quality
- Excel format must have standard column headers
- Phone number formatting assumes Indian format
- Service charges (shipping, making) are filtered from products

## 🚀 Deployment

### Frontend (Vercel)
```bash
cd frontend
npm run build
vercel --prod
```

### Backend (Railway/Render)
```bash
cd backend
# Add Procfile: web: python main.py
# Deploy to Railway or Render
```

## 🤝 Contributing

This is an assignment submission. For educational purposes only.

## 📄 License

MIT License - see [LICENSE](LICENSE) file

## 👨‍💻 Author

**Medidala Aditya**
- Institution: VIT Vellore (B.Tech IT, 2022-26)
- Email: [your.email@example.com]
- LinkedIn: [Your LinkedIn]
- GitHub: [@yourusername](https://github.com/yourusername)

## 🙏 Acknowledgments

- Assignment provided by Swipe
- Google Document AI for OCR
- Google Gemini for LLM extraction
- Mantine UI for components

---

**Assignment Submission for Swipe Software Development Intern (AI) Role**

*Built with ❤️ for Swipe*

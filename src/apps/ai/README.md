# 🤖 AI Intelligence Module

PetCare Artificial Intelligence Module with 3 specialized agents.

## 🎯 Implemented Agents

### 1. Product Intelligence Agent
Generates product descriptions using LLM + RAG (Retrieval-Augmented Generation).

**Features:**
- ✅ Technical descriptions generation (based on similar products)
- ✅ Creative descriptions generation (for new products)
- ✅ Vector search for similar products (ChromaDB)
- ✅ SEO suggestions (title, meta description, tags)
- ✅ Automatic detection of known vs unknown products

**How to use in Admin:**
1. Access **Admin → Store → Products**
2. Select one or more products
3. Choose action: **"🤖 Generate Technical Description (AI)"** or **"✨ Generate Creative Description (AI)"**
4. Description will be generated and saved automatically

### 2. Health Assistant Agent
Analyzes pet health patterns and generates actionable insights.

**Features:**
- ✅ Health pattern detection (seasonality, recurrence)
- ✅ Expired or near-expiration vaccine alerts
- ✅ Health score calculation (0-100)
- ✅ Personalized preventive recommendations
- ✅ Health reports generation

**How to use in Admin:**
1. Access **Admin → Pets → Pets**
2. Select one or more pets
3. Choose action: **"🩺 Analyze Health Patterns (AI)"**
4. Insights and alerts will be generated automatically

### 3. Scheduling Assistant Agent 🆕
Interprets natural language scheduling requests using **Gemini Function Calling**.

**Features:**
- ✅ **Natural language understanding** - understands colloquial Portuguese
- ✅ **Intelligent pet search** - by breed, species, age
- ✅ **Availability checking** - free slots by day/period
- ✅ **Automatic price calculation** - with size-based adjustments
- ✅ **Conversational responses** - friendly and professional tone
- ✅ **Tool execution tracking** - transparency in actions performed

**How to use via API:**

```bash
curl -X POST https://petcare.brunadev.com/api/v1/ai/schedule-intent/ \
  -H "Content-Type: application/json" \
  -d '{
    "user_input": "I need grooming for my 5-year-old Golden Retriever, preferably Saturday morning",
    "customer_id": 1
  }'
```

**Example response:**

```json
{
  "message": "Found Thor! 🐕 We have 3 available slots on Saturday morning: 09:00, 10:30, and 11:00. Grooming for large breed costs R$ 120.00 and takes about 90 minutes. Which time works for you?",
  "tools_executed": [
    {
      "tool_name": "search_customer_pets",
      "arguments": {
        "species": "dog",
        "breed": "golden retriever",
        "age_min": 5,
        "age_max": 5
      },
      "result": [
        {
          "id": 1,
          "name": "Thor",
          "breed": "Golden Retriever",
          "species": "Dog",
          "age": 5,
          "owner_name": "João Silva"
        }
      ],
      "thinking": "Executing search_customer_pets..."
    },
    {
      "tool_name": "check_availability",
      "arguments": {
        "day": "saturday",
        "period": "morning"
      },
      "result": {
        "available_slots": [
          {"time": "09:00", "date": "12/20/2024"},
          {"time": "10:30", "date": "12/20/2024"},
          {"time": "11:00", "date": "12/20/2024"}
        ]
      }
    },
    {
      "tool_name": "calculate_price",
      "arguments": {
        "service_name": "grooming",
        "pet_size": "large"
      },
      "result": {
        "formatted_price": "R$ 120.00",
        "duration_minutes": 90
      }
    }
  ],
  "intent_detected": "book_appointment",
  "confidence_score": 0.95
}
```

**Agent Capabilities:**

| Capability | Input Example |
|------------|---------------|
| Breed search | "my 5-year-old Golden" |
| Species search | "my cat", "my siamese cat" |
| Weekdays (PT/EN) | "saturday", "sábado", "next Tuesday" |
| Time periods | "morning", "afternoon", "evening" |
| ISO dates | "2024-12-20" |
| Keywords | "today", "tomorrow", "hoje" |

## 📊 Admin Visualization

### AI Generated Content
Access **Admin → AI Intelligence → AI Generated Contents** to view:
- Generated content history
- Confidence score
- Acceptance status
- User feedback

### Health Patterns
Access **Admin → AI Intelligence → Health Patterns** to view:
- Patterns detected per pet
- AI recommendations
- Confidence score
- Active/inactive status

## 🔧 Initial Setup

###  1. Configure Google Gemini API Key

```bash
# Get API key at: https://makersuite.google.com/app/apikey
# Add to .env:
GOOGLE_API_KEY=your_api_key_here
```

### 2. Index Existing Products

```bash
docker compose exec web python manage.py index_products
```

This command indexes all products in the vector store (ChromaDB) to enable semantic search.

### 3. Test Scheduling Agent

```bash
docker compose exec web python manage.py shell

from src.apps.ai.agents.scheduling_agent import SchedulingAgentService, SchedulingIntentRequest

service = SchedulingAgentService()
request = SchedulingIntentRequest(
    user_input="I need grooming for my 5-year-old Golden, Saturday morning",
    customer_id=1
)

result = service.generate_intent(request)
print(result.message)
print(f"Confidence: {result.confidence_score}")
print(f"Tools used: {len(result.tools_executed)}")
```

## 🏗️ Architecture

```
src/apps/ai/
├── models.py                    # Models (AIGeneratedContent, HealthPattern, ProductEmbedding)
├── services.py                  # ProductIntelligenceService
├── admin.py                     # Django Admin integration
├── agents/
│   ├── health_agent.py          # HealthAssistantService
│   ├── scheduling_agent.py      # 🆕 SchedulingAgentService
│   └── tools/                   # 🆕 Gemini Function Calling tools
│       ├── search_customer_pets.py
│       ├── check_availability.py
│       └── calculate_price.py
├── embeddings/
│   ├── vector_store.py          # ChromaDB wrapper
│   └── embeddings_service.py    # Sentence Transformers
├── prompts/
│   ├── product_prompts.py       # Prompts for Product Agent
│   ├── health_prompts.py        # Prompts for Health Agent
│   └── scheduling_prompts.py    # 🆕 Prompts for Scheduling Agent
├── api/
│   ├── views.py                 # DRF views
│   ├── serializers.py           # 🆕 DRF serializers
│   └── urls.py                  # API routes
└── management/commands/
    └── index_products.py        # Command to index products
```

## 🔑 Tech Stack

- **LLM:** Google Gemini 2.5 Flash (free up to 1500 req/day)
- **Function Calling:** Gemini native tool use
- **Orchestration:** LangChain 1.1+
- **Embeddings:** Google Gemini Embeddings API (text-embedding-004)
- **Vector DB:** ChromaDB (embedded, no separate server)
- **Cache:** Redis (for embeddings)

## 📈 Metrics

The system automatically tracks:
- **Confidence Score:** AI confidence in generation (0-1)
- **Acceptance Rate:** User acceptance rate
- **Response Time:** Generation response time
- **Cache Hit Rate:** Embeddings cache hit rate

## 🧪 Tests

```bash
# Run all AI module tests
docker compose exec web pytest src/apps/ai/tests/ -v

# Test only Scheduling Agent
docker compose exec web pytest src/apps/ai/tests/test_scheduling_agent.py -v

# With coverage
docker compose exec web pytest src/apps/ai/tests/ --cov=src.apps.ai
```

## 🚀 Next Steps

- [x] REST API endpoint for Scheduling Agent
- [ ] Frontend (Chat Widget) for scheduling
- [ ] WebSocket for response streaming
- [ ] AI metrics dashboard
- [ ] Prompt fine-tuning based on feedback
- [ ] Multi-language support
- [ ] WhatsApp integration for alerts

## 📚 Additional Documentation

- [LangChain Docs](https://python.langchain.com/docs/)
- [Google Gemini API](https://ai.google.dev/docs)
- [Gemini Function Calling](https://ai.google.dev/gemini-api/docs/function-calling)
- [ChromaDB Docs](https://docs.trychroma.com/)
- [Sentence Transformers](https://www.sbert.net/)

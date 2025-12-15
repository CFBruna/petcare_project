# 🤖 AI Intelligence Module

Módulo de Inteligência Artificial do PetCare com 2 agentes especializados.

## 🎯 Agentes Implementados

### 1. Product Intelligence Agent
Gera descrições de produtos usando LLM + RAG (Retrieval-Augmented Generation).

**Funcionalidades:**
- ✅ Geração de descrições técnicas (baseadas em produtos similares)
- ✅ Geração de descrições criativas (para produtos novos)
- ✅ Busca vetorial de produtos similares (ChromaDB)
- ✅ Sugestões de SEO (título, meta description, tags)
- ✅ Detecção automática de produtos conhecidos vs desconhecidos

**Como usar no Admin:**
1. Acesse **Admin → Store → Products**
2. Selecione um ou mais produtos
3. Escolha ação: **"🤖 Gerar Descrição Técnica (IA)"** ou **"✨ Gerar Descrição Criativa (IA)"**
4. A descrição será gerada e salva automaticamente

### 2. Health Assistant Agent
Analisa padrões de saúde dos pets e gera insights acionáveis.

**Funcionalidades:**
- ✅ Detecção de padrões de saúde (sazonalidade, recorrência)
- ✅ Alertas de vacinas vencidas ou próximas do vencimento
- ✅ Cálculo de score de saúde (0-100)
- ✅ Recomendações preventivas personalizadas
- ✅ Geração de relatórios de saúde

**Como usar no Admin:**
1. Acesse **Admin → Pets → Pets**
2. Selecione um ou mais pets
3. Escolha ação: **"🩺 Analisar Padrões de Saúde (IA)"**
4. Insights e alertas serão gerados automaticamente

## 📊 Visualização no Admin

### AI Generated Content
Acesse **Admin → AI Intelligence → AI Generated Contents** para ver:
- Histórico de conteúdo gerado
- Score de confiança
- Status de aceitação
- Feedback dos usuários

### Health Patterns
Acesse **Admin → AI Intelligence → Health Patterns** para ver:
- Padrões detectados por pet
- Recomendações da IA
- Score de confiança
- Status ativo/inativo

## 🔧 Setup Inicial

### 1. Configurar API Key do Google Gemini

```bash
# Obter API key em: https://makersuite.google.com/app/apikey
# Adicionar ao .env:
GOOGLE_API_KEY=your_api_key_here
```

### 2. Indexar Produtos Existentes

```bash
docker compose exec web python manage.py index_products
```

Este comando indexa todos os produtos no vector store (ChromaDB) para permitir busca semântica.

### 3. Testar Geração de Descrição

```bash
docker compose exec web python manage.py shell

from src.apps.ai.services import ProductIntelligenceService, ProductDescriptionRequest

service = ProductIntelligenceService()
request = ProductDescriptionRequest(
    product_name="Ração Golden Fórmula 15kg",
    category="Ração",
    brand="Golden",
    price=189.90,
    mode="technical"
)

result = service.generate_description(request)
print(result.description)
```

## 🏗️ Arquitetura

```
src/apps/ai/
├── models.py                    # Models (AIGeneratedContent, HealthPattern, ProductEmbedding)
├── services.py                  # ProductIntelligenceService
├── admin.py                     # Django Admin integration
├── agents/
│   └── health_agent.py          # HealthAssistantService
├── embeddings/
│   ├── vector_store.py          # ChromaDB wrapper
│   └── embeddings_service.py    # Sentence Transformers
├── prompts/
│   ├── product_prompts.py       # Prompts para Product Agent
│   └── health_prompts.py        # Prompts para Health Agent
└── management/commands/
    └── index_products.py        # Command para indexar produtos
```

## 🔑 Stack Técnica

- **LLM:** Google Gemini Pro (gratuito até 60 req/min)
- **Embeddings:** Sentence Transformers (all-MiniLM-L6-v2)
- **Vector DB:** ChromaDB (embedded, sem servidor separado)
- **Orchestration:** LangChain
- **Cache:** Redis (para embeddings)

## 📈 Métricas

O sistema registra automaticamente:
- **Confidence Score:** Confiança da IA na geração (0-1)
- **Acceptance Rate:** Taxa de aceitação pelos usuários
- **Response Time:** Tempo de resposta das gerações
- **Cache Hit Rate:** Taxa de acerto do cache de embeddings

## 🧪 Testes

```bash
# Rodar testes do módulo AI
docker compose exec web pytest src/apps/ai/tests/ -v

# Com coverage
docker compose exec web pytest src/apps/ai/tests/ --cov=src.apps.ai
```

## 🚀 Próximos Passos

- [ ] API REST endpoints para integração externa
- [ ] Dashboard de métricas de IA
- [ ] Fine-tuning de prompts baseado em feedback
- [ ] Suporte a múltiplos idiomas
- [ ] Integração com WhatsApp para alertas

## 📚 Documentação Adicional

- [LangChain Docs](https://python.langchain.com/docs/)
- [Google Gemini API](https://ai.google.dev/docs)
- [ChromaDB Docs](https://docs.trychroma.com/)
- [Sentence Transformers](https://www.sbert.net/)

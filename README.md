# PetCare - Sistema de Gestão para Pet Shops

[![Django CI](https://github.com/CFBruna/petcare_project/actions/workflows/ci.yml/badge.svg)](https://github.com/CFBruna/petcare_project/actions/workflows/ci.yml)

> Um sistema web completo para gestão de pet shops, desenvolvido com foco em boas práticas, arquitetura robusta e qualidade de código.

Este projeto utiliza Django em um ambiente conteinerizado com Docker, oferecendo um portal administrativo completo, uma API REST bem documentada e um fluxo de trabalho de desenvolvimento automatizado com testes e integração contínua.

---

## ✨ Funcionalidades Principais

* **Gestão de Clientes e Pets:** Cadastro completo de tutores e seus animais.
* **Agendamento de Serviços:** Sistema de agendamento com base em horários disponíveis e duração dos serviços.
* **Catálogo de Produtos:** Gerenciamento de produtos, categorias, marcas e lotes com controle de estoque.
* **Promoções:** Criação de promoções manuais e automáticas baseadas na data de validade dos produtos.
* **Ponto de Venda (PDV):** Módulo para registrar vendas, com baixa automática de estoque.
* **Painel Administrativo (Dashboard):** Visão geral com métricas de faturamento e agendamentos.
* **Tarefas Agendadas (Celery Beat):** Geração de relatórios diários de vendas e promoções.

---

## 📚 Documentação da API

O projeto segue o padrão OpenAPI e a documentação da API é gerada automaticamente pelo `drf-spectacular`. Após iniciar o projeto, você pode acessar:

* **Swagger UI:** `http://127.0.0.1:8000/api/v1/schema/swagger-ui/`
* **ReDoc:** `http://127.0.0.1:8000/api/v1/schema/redoc/`

---

## ✅ Qualidade e Automação

Este projeto utiliza um fluxo de trabalho de Integração Contínua (CI) com o **GitHub Actions**. A cada `push` ou `pull request` para a branch `main`, o seguinte pipeline é executado:

1.  **Instalação de Dependências:** O ambiente é criado e as dependências do `requirements.txt` são instaladas.
2.  **Verificação de Tipagem:** O `Mypy` é executado para garantir a segurança de tipos do código.
3.  **Verificação de Linting:** O `Ruff` é executado para garantir a qualidade e o padrão de formatação.
4.  **Execução dos Testes:** A suíte de testes (`pytest`) é executada, com um relatório de cobertura.

---

## 🛠️ Stack de Tecnologias

* **Backend:** Django, Django Rest Framework
* **Banco de Dados:** PostgreSQL
* **Filas e Cache:** Celery, Redis
* **Ambiente:** Docker, Docker Compose
* **Qualidade de Código:** Ruff, Mypy, Pre-commit
* **Testes:** Pytest, pytest-django, factory-boy
* **Documentação da API:** drf-spectacular (OpenAPI)

---

## 🚀 Como Rodar o Projeto

### Pré-requisitos

* [Docker](https://www.docker.com/products/docker-desktop/)
* [Git](https://git-scm.com/)

### Passos

1.  **Clone o repositório:**
    ```bash
    git clone [https://github.com/CFBruna/petcare_project.git](https://github.com/CFBruna/petcare_project.git)
    cd petcare_project
    ```

2.  **Crie e configure o arquivo de ambiente:**
    ```bash
    cp .env.example .env
    ```
    > **Importante:** Abra o arquivo `.env` e gere uma nova `SECRET_KEY`. Você pode usar um gerador online ou o próprio Django para isso.

3.  **Construa e suba os containers Docker:**
    ```bash
    docker-compose up --build -d
    ```

4.  **Rode as migrações (em um novo terminal):**
    ```bash
    docker-compose exec web python manage.py migrate
    ```

5.  **Crie um superusuário para acessar o Admin:**
    ```bash
    docker-compose exec web python manage.py createsuperuser
    ```

6.  **(Opcional) Popule o banco de dados com dados de exemplo:**
    Para ter uma experiência mais realista ao explorar o admin, use o comando abaixo.
    ```bash
    docker-compose exec web python manage.py seed_db
    ```

7.  **Acesse a aplicação:**
    * **Admin:** `http://127.0.0.1:8000/admin/`
    * **API (Swagger):** `http://127.0.0.1:8000/api/v1/schema/swagger-ui/`

---

## 🧪 Rodando os Testes

Para executar a suíte de testes completa e gerar um relatório de cobertura, utilize o comando:

```bash
docker-compose exec web pytest --cov
```

## 📄 Licença

Este projeto está sob a licença MIT. Veja o arquivo [LICENSE](LICENSE) para mais detalhes.

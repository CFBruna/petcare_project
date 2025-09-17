# PetCare - Sistema de Gestão para Pet Shops

[![Django CI](https://github.com/CFBruna/petcare_project/actions/workflows/ci.yml/badge.svg)](https://github.com/CFBruna/petcare_project/actions/workflows/ci.yml)

> Um sistema web completo para gestão de pet shops, desenvolvido com foco em boas práticas, arquitetura robusta e qualidade de código, totalmente hospedado em produção na AWS.

---

## 🚀 Demonstração Ao Vivo (Live Demo)

Você pode testar a aplicação ao vivo, hospedada em uma arquitetura de produção na AWS.

* **Link Principal:** **[http://petcare.brunadev.com](http://petcare.brunadev.com)**
* **Acesso ao Admin:** **[http://petcare.brunadev.com/admin/](http://petcare.brunadev.com/admin/)**

**Credenciais para teste:**
* **Usuário:** `tester`
* **Senha:** `tester1234`

---

### ✨ Demonstração em Vídeo

Assista a um vídeo de menos de 2 minutos que demonstra as principais funcionalidades, a arquitetura e o pipeline de qualidade do PetCare.

[<img src="https://github.com/user-attachments/assets/4a9bc390-a421-40e7-8dbe-efa585e00ebe" width="100%">](https://youtu.be/hD8qak2FAoQ)

---

## 🏗️ Arquitetura de Produção (AWS)

Este projeto está em produção utilizando uma arquitetura moderna e escalável na nuvem da AWS:

* **Computação:** **EC2** para rodar a aplicação containerizada com Docker.
* **Banco de Dados:** **RDS (PostgreSQL)** para um banco de dados relacional gerenciado e seguro.
* **Cache & Tarefas Assíncronas:** **ElastiCache (Redis)** para gerenciar o Celery.
* **Servidor Web & Proxy Reverso:** **Nginx** para servir arquivos estáticos e gerenciar o tráfego.
* **DNS:** **Route 53** para gerenciamento dos domínios.
* **Containerização:** **Docker e Docker Compose** para garantir consistência entre os ambientes.

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

O projeto segue o padrão OpenAPI e a documentação da API é gerada automaticamente. Na versão de produção, a documentação pode ser acessada nos seguintes links:

* **Swagger UI:** `http://petcare.brunadev.com/api/v1/schema/swagger-ui/`
* **ReDoc:** `http://petcare.brunadev.com/api/v1/schema/redoc/`

---

## ✅ Qualidade e Automação

Este projeto utiliza um fluxo de trabalho de Integração Contínua (CI) com o **GitHub Actions**. A cada `push` ou `pull request` para a branch `main`, o seguinte pipeline é executado:

1.  **Instalação de Dependências:** O ambiente é criado e as dependências são instaladas.
2.  **Verificação de Tipagem (Mypy):** Garante a segurança de tipos do código.
3.  **Verificação de Linting (Ruff):** Garante a qualidade e o padrão de formatação.
4.  **Execução dos Testes (Pytest):** A suíte de testes é executada e um relatório de cobertura é gerado.

---

## 🛠️ Stack de Tecnologias

* **Backend:** Django, Django Rest Framework, Gunicorn
* **Banco de Dados:** PostgreSQL, Redis
* **Filas e Cache:** Celery
* **Infraestrutura:** Docker, Docker Compose, Nginx, AWS (EC2, RDS, ElastiCache, Route 53)
* **Qualidade de Código:** Ruff, Mypy, Pre-commit
* **Testes:** Pytest, pytest-django, factory-boy
* **Documentação da API:** drf-spectacular (OpenAPI)

---

## 🚀 Como Rodar o Projeto (Desenvolvimento Local)

Estas instruções são para rodar o projeto em um ambiente de desenvolvimento na sua máquina.

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
    > **Importante:** Abra o arquivo `.env` e preencha as variáveis necessárias, como a `SECRET_KEY`.

3.  **Construa e suba os containers Docker:**
    ```bash
    docker-compose up --build -d
    ```

4.  **Rode as migrações:**
    ```bash
    docker-compose exec web python manage.py migrate
    ```

5.  **Crie um superusuário:**
    ```bash
    docker-compose exec web python manage.py createsuperuser
    ```

6.  **Acesse a aplicação:**
    * **Admin:** `http://127.0.0.1:8000/admin/`

---

## 🧪 Rodando os Testes

Para executar a suíte de testes completa e gerar um relatório de cobertura, utilize o comando:

```bash
docker-compose exec web pytest --cov
```

## 📄 Licença

Este projeto está sob a licença MIT. Veja o arquivo [LICENSE](LICENSE) para mais detalhes.

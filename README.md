# PetCare - Sistema de Gestão para Pet Shops

[![Django CI](https://github.com/CFBruna/petcare_project/actions/workflows/ci.yml/badge.svg)](https://github.com/CFBruna/petcare_project/actions/workflows/ci.yml)

> Um sistema web completo para gestão de pet shops, permitindo o gerenciamento de clientes, pets, agendamentos de serviços e um catálogo de produtos.

Este projeto foi desenvolvido com foco em boas práticas de arquitetura de software, utilizando Django em um ambiente conteinerizado com Docker. A aplicação oferece um portal administrativo robusto e um fluxo de trabalho de desenvolvimento automatizado com testes e integração contínua.

---

## ✅ Qualidade e Automação

Este projeto utiliza um fluxo de trabalho de Integração Contínua (CI) com o **GitHub Actions**. A cada `push` ou `pull request` para a branch `main`, o seguinte pipeline é executado automaticamente:

1.  **Instalação de Dependências:** O ambiente é criado e as dependências são instaladas.
2.  **Verificação de Linting:** O `Ruff` é executado para garantir a qualidade do código.
3.  **Execução dos Testes:** A suíte de testes é executada com `pytest`.

---

## 🛠️ Stack de Tecnologias

* **Backend:** Django
* **Banco de Dados:** PostgreSQL
* **Ambiente:** Docker, Docker Compose
* **Qualidade de Código:** Ruff, Pre-commit
* **Testes:** Pytest, pytest-django, pytest-cov, factory-boy

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

3.  **Construa e suba os containers Docker:**
    ```bash
    docker-compose up --build
    ```

4.  **Rode as migrações (em um novo terminal):**
    ```bash
    docker-compose exec web python manage.py migrate
    ```

5.  **Crie um superusuário para acessar o Admin:**
    ```bash
    docker-compose exec web python manage.py createsuperuser
    ```

6.  **Acesse a aplicação:**
    Abra seu navegador e acesse `http://127.0.0.1:8000/admin/`.

---

## 📄 Licença

Este projeto está sob a licença MIT. Veja o arquivo [LICENSE](LICENSE) para mais detalhes.

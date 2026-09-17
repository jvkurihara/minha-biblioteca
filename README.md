# Minha Biblioteca

Um organizador pessoal de leituras feito com **Python**, **HTML/CSS/JavaScript** e **SQLite**. Cadastre livros, acompanhe o que está lendo e registre suas avaliações. Funciona localmente e não exige contas nem serviços externos.

## Recursos

- Cadastro, edição e exclusão de livros
- Estados: quero ler, lendo e concluído
- Nota de 1 a 5 estrelas para livros concluídos
- Busca e filtro instantâneos
- Resumo da coleção na página inicial
- Dados persistidos em `data/library.db`

## Executar

Requer Python 3.10 ou superior. Não há dependências externas.

```bash
python app.py
```

Acesse http://localhost:8000. Para mudar a porta, defina `PORT` antes de iniciar o programa.

## Testes

```bash
python -m unittest discover -s tests -v
```

## Estrutura

```text
app.py             Servidor HTTP e API JSON
database.py        Persistência SQLite e validação
static/            Interface web
tests/             Testes da API e do banco
data/              Banco local criado automaticamente
```

## API

| Método | Rota | Ação |
| --- | --- | --- |
| GET | `/api/books` | Lista livros |
| POST | `/api/books` | Cria livro |
| PATCH | `/api/books/{id}` | Atualiza livro |
| DELETE | `/api/books/{id}` | Exclui livro |

Exemplo de criação:

```json
{"title":"Dom Casmurro","author":"Machado de Assis","status":"quero-ler","rating":null}
```

Os campos `title` e `author` são obrigatórios. `status` aceita `quero-ler`, `lendo` ou `concluido`. `rating` aceita um inteiro de 1 a 5 ou `null`.

## Licença

MIT. Consulte [LICENSE](LICENSE).


const list = document.querySelector('#book-list');
const empty = document.querySelector('#empty-state');
const message = document.querySelector('#message');
const dialog = document.querySelector('#book-dialog');
const form = document.querySelector('#book-form');
const statusInput = document.querySelector('#status');
const ratingField = document.querySelector('#rating-field');
const ratingInput = document.querySelector('#rating');
const filterInput = document.querySelector('#filter');
const searchInput = document.querySelector('#search');
let books = [];
let editingId = null;

const labels = { 'quero-ler': 'Quero ler', lendo: 'Lendo', concluido: 'Concluído' };

async function request(path, options = {}) {
  const response = await fetch(path, { ...options, headers: { 'Content-Type': 'application/json', ...options.headers } });
  if (response.status === 204) return null;
  const data = await response.json();
  if (!response.ok) throw new Error(data.error || 'Ocorreu um erro. Tente novamente.');
  return data;
}

function showError(text) {
  message.textContent = text;
  message.hidden = false;
}

function clearError() {
  message.hidden = true;
  message.textContent = '';
}

function makeElement(tag, className, text) {
  const element = document.createElement(tag);
  if (className) element.className = className;
  if (text != null) element.textContent = text;
  return element;
}

function renderCard(book) {
  const card = makeElement('article', 'book-card');
  const top = makeElement('div', 'card-top');
  top.append(makeElement('div', `book-icon ${book.status}`), makeElement('span', `badge ${book.status}`, labels[book.status]));
  card.append(top, makeElement('h3', '', book.title), makeElement('p', '', book.author));
  const bottom = makeElement('div', 'card-bottom');
  bottom.append(makeElement('span', 'rating', book.rating ? '★'.repeat(book.rating) + '☆'.repeat(5 - book.rating) : 'Sem avaliação'));
  const actions = makeElement('div', 'card-actions');
  const edit = makeElement('button', '', 'Editar');
  edit.type = 'button';
  edit.setAttribute('aria-label', `Editar ${book.title}`);
  edit.addEventListener('click', () => openDialog(book));
  const remove = makeElement('button', '', 'Excluir');
  remove.type = 'button';
  remove.setAttribute('aria-label', `Excluir ${book.title}`);
  remove.addEventListener('click', () => deleteBook(book));
  actions.append(edit, remove);
  bottom.append(actions);
  card.append(bottom);
  return card;
}

function render() {
  document.querySelector('#total-count').textContent = books.length;
  document.querySelector('#reading-count').textContent = books.filter(book => book.status === 'lendo').length;
  document.querySelector('#finished-count').textContent = books.filter(book => book.status === 'concluido').length;
  const query = searchInput.value.trim().toLocaleLowerCase('pt-BR');
  const visible = books.filter(book => (filterInput.value === 'todos' || book.status === filterInput.value)
    && `${book.title} ${book.author}`.toLocaleLowerCase('pt-BR').includes(query));
  list.replaceChildren(...visible.map(renderCard));
  empty.hidden = books.length !== 0;
  if (books.length && !visible.length) {
    const noResults = makeElement('p', 'no-results', 'Nenhum livro encontrado para esta busca.');
    list.append(noResults);
  }
}

async function loadBooks() {
  try {
    books = await request('/api/books');
    clearError();
    render();
  } catch (error) {
    showError(error.message);
  }
}

function toggleRating() {
  const finished = statusInput.value === 'concluido';
  ratingField.hidden = !finished;
  if (!finished) ratingInput.value = '';
}

function openDialog(book = null) {
  editingId = book?.id ?? null;
  form.reset();
  document.querySelector('#form-error').hidden = true;
  document.querySelector('#dialog-title').textContent = book ? 'Editar livro' : 'Novo livro';
  document.querySelector('#save-button').textContent = book ? 'Salvar alterações' : 'Salvar livro';
  if (book) {
    form.elements.title.value = book.title;
    form.elements.author.value = book.author;
    statusInput.value = book.status;
    ratingInput.value = book.rating ?? '';
  }
  toggleRating();
  dialog.showModal();
  form.elements.title.focus();
}

async function deleteBook(book) {
  if (!confirm(`Excluir “${book.title}” da sua estante?`)) return;
  try {
    await request(`/api/books/${book.id}`, { method: 'DELETE' });
    await loadBooks();
  } catch (error) {
    showError(error.message);
  }
}

form.addEventListener('submit', async event => {
  event.preventDefault();
  const errorBox = document.querySelector('#form-error');
  const payload = {
    title: form.elements.title.value.trim(),
    author: form.elements.author.value.trim(),
    status: statusInput.value,
    rating: statusInput.value === 'concluido' && ratingInput.value ? Number(ratingInput.value) : null,
  };
  if (!payload.title || !payload.author) {
    errorBox.textContent = 'Preencha o título e o autor.';
    errorBox.hidden = false;
    return;
  }
  try {
    await request(editingId ? `/api/books/${editingId}` : '/api/books', {
      method: editingId ? 'PATCH' : 'POST', body: JSON.stringify(payload),
    });
    dialog.close();
    await loadBooks();
  } catch (error) {
    errorBox.textContent = error.message;
    errorBox.hidden = false;
  }
});

document.querySelector('#add-button').addEventListener('click', () => openDialog());
document.querySelector('#empty-add-button').addEventListener('click', () => openDialog());
document.querySelector('#close-dialog').addEventListener('click', () => dialog.close());
document.querySelector('#cancel-button').addEventListener('click', () => dialog.close());
statusInput.addEventListener('change', toggleRating);
filterInput.addEventListener('change', render);
searchInput.addEventListener('input', render);
loadBooks();


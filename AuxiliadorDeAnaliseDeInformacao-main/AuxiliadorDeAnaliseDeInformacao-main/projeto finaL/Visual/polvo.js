(() => {
  // Caminho da imagem: fica na mesma pasta deste script
  const base = document.currentScript ? document.currentScript.src : location.href;
  const IMG = new URL('polvo-branco.png', base).href;

  // ---------- Polvos nadando no topo (área escura) ----------
  const hero = document.querySelector('.hero') || document.body;
  const faixa = document.createElement('div');
  faixa.className = 'polvo-faixa';
  faixa.setAttribute('aria-hidden', 'true');

  const BOLHAS = [ // posição (% da figura), tamanho, duração, atraso
    ['4%', '34%', '14px', '4.6s', '0s'],
    ['10%', '20%', '9px', '5.2s', '1.4s'],
    ['2%', '12%', '6px', '4.2s', '2.6s'],
    ['14%', '40%', '8px', '5.6s', '3.3s'],
    ['6%', '26%', '5px', '4.8s', '0.8s'],
  ];

  function criarPolvo(classe) {
    const x = document.createElement('div');
    x.className = 'polvo-x ' + classe;
    const y = document.createElement('div');
    y.className = 'polvo-y';
    const fig = document.createElement('div');
    fig.className = 'polvo-fig';
    for (const cls of ['p-cabeca', 'p-cauda']) {
      const img = document.createElement('img');
      img.className = cls;
      img.src = IMG;
      img.alt = '';
      img.draggable = false;
      fig.append(img);
    }
    BOLHAS.forEach(([l, t, s, d, dl]) => {
      const b = document.createElement('span');
      b.className = 'bolha';
      b.style.cssText = `--l:${l};--t:${t};--s:${s};--d:${d};--dl:${dl}`;
      fig.append(b);
    });
    y.append(fig);
    x.append(y);
    return x;
  }

  faixa.append(criarPolvo('polvo-grande'), criarPolvo('polvo-pequeno'));
  hero.prepend(faixa);

  // largura da área em px (usada pela animação de ida e volta)
  const medir = () => faixa.style.setProperty('--cw', faixa.clientWidth + 'px');
  medir();
  if ('ResizeObserver' in window) new ResizeObserver(medir).observe(faixa);
  else addEventListener('resize', medir);

  // ---------- Lupa ao passar o mouse nas claims ----------
  if (!matchMedia('(hover: hover)').matches) return;

  const lupa = document.createElement('div');
  lupa.className = 'lupa-cursor';
  lupa.setAttribute('aria-hidden', 'true');
  lupa.innerHTML =
    '<svg viewBox="0 0 64 64" fill="none" stroke-linecap="round" xmlns="http://www.w3.org/2000/svg">' +
    '<defs><linearGradient id="lupa-g" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#2f4b73"/><stop offset="1" stop-color="#4b93cf"/></linearGradient></defs>' +
    '<circle cx="26" cy="26" r="19" fill="rgba(75,147,207,.12)" stroke="url(#lupa-g)" stroke-width="3.2"/>' +
    '<path d="M14 24 A13 13 0 0 1 24 13" stroke="#4b93cf" stroke-width="2.4" opacity=".75"/>' +
    '<path d="M40 40 L57 57" stroke="url(#lupa-g)" stroke-width="5.5"/>' +
    '</svg>';
  document.body.append(lupa);

  let ativa = false;
  const mover = (e) => { lupa.style.transform = `translate3d(${e.clientX - 57}px, ${e.clientY - 57}px, 0)`; };
  const claimDe = (el) => (el && el.closest ? el.closest('a.claim-grifada') : null);

  document.addEventListener('pointerover', (e) => {
    if (e.pointerType !== 'mouse' || !claimDe(e.target)) return;
    ativa = true; mover(e); lupa.classList.add('ativa');
  });
  document.addEventListener('pointerout', (e) => {
    const a = claimDe(e.target);
    if (a && !a.contains(e.relatedTarget)) { ativa = false; lupa.classList.remove('ativa'); }
  });
  document.addEventListener('pointermove', (e) => { if (ativa) mover(e); });
})();

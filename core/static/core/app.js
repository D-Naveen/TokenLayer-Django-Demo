document.addEventListener('DOMContentLoaded',()=>{
  document.querySelectorAll('.demo-account').forEach(button=>button.addEventListener('click',()=>{
    const u=document.querySelector('input[name="username"]'),
    p=document.querySelector('input[name="password"]');
    if(u&&p){u.value=button.dataset.user;p.value=button.dataset.pass;u.focus();
      document.querySelectorAll('.demo-account').forEach(x=>x.classList.remove('selected'));
      button.classList.add('selected')}
  }));
  document.querySelectorAll('.uppercase-input').forEach(input=>input.addEventListener('input',
    ()=>{input.value=input.value.toUpperCase()}));
  document.querySelectorAll('input[type="file"]').forEach(input=>
    input.addEventListener('change',()=>{if(input.files.length)
      {const label=input.closest('.field').querySelector('label');if(label)label.dataset.filename=input.files[0].name}}));
});

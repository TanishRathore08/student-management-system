const signUpButton = document.getElementById('signUp');
const signInButton = document.getElementById('signIn');
const container = document.getElementById('container');

if (signUpButton) {
  signUpButton.addEventListener('click', () => {
    container && container.classList.add("right-panel-active");
  });
}

if (signInButton) {
  signInButton.addEventListener('click', () => {
    container && container.classList.remove("right-panel-active");
  });
}

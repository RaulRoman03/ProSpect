// Función para manejar el login (existente)
document.getElementById('loginForm')?.addEventListener('submit', function(e) {
    e.preventDefault();
    
    const email = document.getElementById('email').value;
    const password = document.getElementById('password').value;
    const role = document.getElementById('role').value;
    
    // Validaciones básicas
    if (!email || !password || !role) {
        alert('Por favor completa todos los campos');
        return;
    }
    
    if (!email.includes('@') || !email.includes('.')) {
        alert('Por favor ingresa un email válido');
        return;
    }
    
    if (password.length < 6) {
        alert('La contraseña debe tener al menos 6 caracteres');
        return;
    }
    
    // Redirección según el rol
    switch(role) {
        case 'player':
            window.location.href = 'player.html';
            break;
        case 'coach':
            window.location.href = 'coach.html';
            break;
        case 'recruiter':
            window.location.href = 'recruiter.html';
            break;
        default:
            alert('Tipo de usuario no válido');
    }
});

// Función para manejar el logout
document.getElementById('logout')?.addEventListener('click', function(e) {
    e.preventDefault();
    
    // Aquí podrías añadir lógica para limpiar localStorage/sessionStorage
    // localStorage.removeItem('token');
    // localStorage.removeItem('userData');
    
    // Redirigir al index
    window.location.href = 'index.html';
});

// Asegurar que el evento se añade a todos los botones de logout
document.querySelectorAll('#logout').forEach(button => {
    button.addEventListener('click', function(e) {
        e.preventDefault();
        window.location.href = 'index.html';
    });
});
$("document").ready(function() {
    // Affichage mobile du menu | affiche/cache le menu contenant la liste des catégories 
    // en appuyant sur le burger/les trois traits
    $(".navbar-burger").click(function() {
        $(".navbar-burger").toggleClass("is-active");
        $(".navbar-menu").toggleClass("is-active");
    });
    $(".button").click(function() {
        $(this).addClass("is-loading");
    });
    // Redirige vers la page tapé dans la barre de recherche | recheche brut, possible d'amélioration avec 
    // auto-complétion, créer une page web "page n'existe pas", recherche par motsclés, page avec une liste des 
    // pages web possibles en fonction de ce que entre l'utilisateur
    // ex: "R101" -> ./HTML/R101.html
    $("#rechercher").keyup(function(e) {
        if(e.keyCode == 13) {location.href = $(this).val().toUpperCase() + ".html"}
    });
});

// Permet l'affichage du LaTeX avec comme balise délimiteur "$"
MathJax = {
    tex: {
      inlineMath: [['$', '$']]
    }
  };
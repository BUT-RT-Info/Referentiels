$("document").ready(function() {
    // Affichage mobile du menu | affiche/cache le menu contenant la liste des catégories 
    // en appuyant sur le burger/les trois traits
    $(".navbar-burger").click(function() {
        $(".navbar-burger").toggleClass("is-active");
        $(".navbar-menu").toggleClass("is-active");
        // Détails visuel du bouton recherche
        $("#rechercheBouton").toggleClass("is-rounded is-fullwidth is-primary")
    });
    // Bouton suivant et précédent qui s'affiche en loading lorsque l'utilisateur change de page
    $("a.button").click(function() {
        $(this).addClass("is-loading");
    });
    // Redirige vers la page tapé dans la barre de recherche | recheche brut, possible d'amélioration avec 
    // auto-complétion, créer une page web "page n'existe pas", recherche par motsclés, page avec une liste des 
    // pages web possibles en fonction de ce que entre l'utilisateur
    // ex: "R101" -> ./HTML/R101.html
    $("#rechercheBouton").click(function() {
        $("#rechercheBoite").addClass("is-active")
    });

    // Gestion de la fermeture de la boite de recherche
    $(".modal-background").click(function() {
        $("#rechercheBoite").removeClass("is-active")
    });
    $("#rechercheBoite-fermer").click(function() {
        $("#rechercheBoite").removeClass("is-active")
    });

    $("#rechercher").keyup(function(e) {
        var recherche = $(this).val();
        if(recherche.length != 0) {
            var resultats = idx.search(recherche);
            if(resultats.length != 0) {
                $("#rechercheResultats").empty();
                resultats.forEach(function(res) {
                    $("#rechercheResultats").append('<a href="' + documents[res.ref]["url"] + '"><p class="title">' + documents[res.ref]["titre"] + '</p></a>')
                    $("#rechercheResultats").append('<p class="subtitle">' + documents[res.ref]["code"] + '</p>')
                });
            } else {$("#rechercheResultats").html('<p class="has-text-centered">Pas de résultats</p>')}
        } else {
            $("#rechercheResultats").html('<p class="has-text-centered">Pas de résultats</p>')
        }

    });
});

// Documents avec toutes les informations nécessaire pour la recherche
var documents = {{documents}}

var idx = lunr(function() {
    this.ref("code")
    this.field("code")
    this.field("motscles")
    this.field("diminutif")
    this.field("titre")

    for(var cle in documents) {
        this.add(documents[cle])
    }
})

// Permet l'affichage du LaTeX avec comme balise délimiteur "$"
// Le menu contextuel de MathJax a été désactivé
MathJax = {
    tex: {
      inlineMath: [['$', '$']]
    },
    options: {
        enableMenu: false
      }
  };
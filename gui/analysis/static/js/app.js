var challengerApp = angular.module('challengerApp',
  ['ui.router', 'ui.bootstrap', 'toastr', 'ngResource',
    'challengerApp.controllers', 'challengerApp.services'])

angular.module('challengerApp').config(function ($stateProvider, $httpProvider) {
  $stateProvider.state('home', {
    url: '/',
    views: {
      'main-menu@': main_menu(),
      'main-content@': {
        templateUrl: 'static/partials/home.html'
      }
    }
  }).state('files_view', {
    url: '/files/{path:.*}',
    views: {
      'main-menu@': main_menu(),
      'main-content@': {
        templateUrl: 'static/partials/experiments.html',
        controller: 'ExperimentController'
      }
    }
  })
}).run(function ($rootScope, $state, toastr) {
  // load the home page by default
  $state.go('home')
})

function main_menu () {
  return {
    templateUrl: 'static/partials/menu.html',
    controller: 'MenuController'
  }
}

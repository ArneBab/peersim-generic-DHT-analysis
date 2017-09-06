angular.module('challengerApp.controllers', [])
  .controller('ExperimentController', function ($scope, $stateParams, ExperimentService, MetricService) {
    $scope.experiment = ExperimentService.get({id: $stateParams.id})
    
    // load the routing choice graph data
    MetricService.get({id: $stateParams.id, metric: 'stats.json'}).$promise.then(function (result) {
      $scope.labels_1 = result.labels
      $scope.series_1 = result.series
      $scope.data_1 = result.data
    })
    $scope.options_1 = {
      title: {
        display: true,
        text: 'Routing Choices - Stacked'
      },
      responsive: true,
      scales: {
        yAxes: [
          {
            stacked: true
          }
        ]
      }
    }

    // load the routing choice graph data
    MetricService.get({id: $stateParams.id, metric: 'path_histo.json'}).$promise.then(function (result) {
      $scope.labels_2 = result.labels
      $scope.series_2 = result.series
      $scope.data_2 = result.data
    })
    $scope.options_2 = {
      title: {
        display: true,
        text: 'Path Lengths Histogram'
      },
      responsive: true
    }

  }).controller('MenuController', function ($scope, $state, ExperimentService) {
  // Build the menu tree from the experiment data
  var builder = function (path_list, path_index, search_items, experiment) {
    if (path_index >= path_list.length)
      return
    path = path_list[path_index]
    item = search_items.find(function (i) {
      return i.label === path
    })
    if (!item) {
      item = {label: path, children: []}
      if (path_index === path_list.length - 1) {
        item.data = experiment
      }
      search_items.push(item)
    }
    return builder(path_list, path_index + 1, item.children, experiment)
  }
  ExperimentService.query().$promise.then(function (result) {
    for (var i = 0; i < result.items.length; i++)
      builder(result.items[i].path.split('/'), 0, $scope.tree, result.items[i])
  })
  // end
  $scope.tree = []
  $scope.tree_handler = function (branch) {
    if (branch.data)
      $state.go('experiments_view', { id: branch.data.id })
  }
})

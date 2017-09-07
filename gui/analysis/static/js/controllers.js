angular.module('challengerApp.controllers', [])
  .controller('ExperimentController', function ($scope, $stateParams, ExperimentService, MetricService) {
    $scope.experiment = ExperimentService.get({id: $stateParams.id})
    $scope.graphs = []

    // load the routing choice graph data
    MetricService.get({id: $stateParams.id, metric: 'stats.json'}).$promise.then(function (result) {
      result.options = stacked_graph_options('Routing Choices: Stacked')
      result.title = 'Routing choice picked'
      result.type = 'line'
      $scope.graphs.push(result)
    })

    // load the routing choice graph data
    MetricService.get({id: $stateParams.id, metric: 'path_histo.json'}).$promise.then(function (result) {
      result.options = basic_graph_options('Path Lengths: Histogram')
      result.title = 'Path lengths'
      result.type = 'bar'
      $scope.graphs.push(result)
    })
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

function basic_graph_options (title) {
  return {
    title: {
      display: true,
      text: title
    },
    responsive: true
  }
}

function stacked_graph_options (title) {
  return {
    title: {
      display: true,
      text: title
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
}

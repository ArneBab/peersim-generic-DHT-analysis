angular.module('challengerApp.controllers', [])
  .controller('ExperimentController', function ($scope, $stateParams, $uibModal, ExperimentService, MetricService) {
    $scope.id = $stateParams.id
    $scope.experiment = ExperimentService.get({id: $stateParams.id})
    $scope.graphs = {'routing':[],'adversary':[], 'sender_set':[], 'anonymity':[]}
    $scope.can_show = function (items) {
      var result = {}
      angular.forEach(items, function (value, key) {
        if (!key.startsWith('_')) {
          result[key] = value
        }
      })
      return result
    }

    // load the routing choice graph data
    MetricService.get({id: $stateParams.id, metric: 'stats.json'}).$promise.then(function (result) {
      result.options = stacked_graph_options('Routing Preferences Taken: Stacked')
      result.type = 'line'
      result.id =0
      $scope.graphs['routing'].push(result)
    })

    // load the routing choice graph data
    MetricService.get({id: $stateParams.id, metric: 'path_histo.json'}).$promise.then(function (result) {
      result.options = basic_graph_options('Path Lengths (Hops): Histogram')
      result.type = 'bar'
      result.id =1
      $scope.graphs['routing'].push(result)
    })

    // load the intercept hop graph data
    MetricService.get({id: $stateParams.id, metric: 'intercept.json'}).$promise.then(function (result) {
      result.options = basic_graph_options('Adversary Intercept at Hop: Histogram')
      result.type = 'bar'
      result.id =2
      $scope.graphs['adversary'].push(result)
    })

    // load the intercept hop graph data
    MetricService.get({id: $stateParams.id, metric: 'intercept_calculated.json'}).$promise.then(function (result) {
      result.options = basic_graph_options('Adversary Intercept at Hop for Calculated: Histogram')
      result.type = 'bar'
      result.id =3
      $scope.graphs['adversary'].push(result)
    })

    // load the sender set graph data
    MetricService.get({id: $stateParams.id, metric: 'sender_set_size.json'}).$promise.then(function (result) {
      result.options = basic_graph_options('Sender Set Size: Histogram')
      result.type = 'bar'
      result.id =4
      $scope.graphs['sender_set'].push(result)
    })

    // load the sender set by intercept hop graph data
    MetricService.get({id: $stateParams.id, metric: 'sender_set_size_by_hop.json'}).$promise.then(function (result) {
      result.options = basic_graph_options('Sender Set Size by Intercepted at Hop: Average')
      result.type = 'line'
      result.id =5
      $scope.graphs['sender_set'].push(result)
    })

    // load the entropy graph data
    MetricService.get({id: $stateParams.id, metric: 'entropy.json'}).$promise.then(function (result) {
      result.options = basic_graph_options('Entropy: Histogram')
      result.type = 'bar'
      result.id =06
      $scope.graphs['anonymity'].push(result)
    })

    // load the sender set by intercept hop graph data
    MetricService.get({id: $stateParams.id, metric: 'entropy_by_hop.json'}).$promise.then(function (result) {
      result.options = basic_graph_options('Entropy by Intercepted at Hop: Average')
      result.type = 'line'
      result.id =7
      $scope.graphs['anonymity'].push(result)
    })

    MetricService.get({id: $stateParams.id, metric: 'top_rank_set_size_by_hop.json'}).$promise.then(function (result) {
      result.options = basic_graph_options('Top Ranked Sender Set Size by Intercepted at Hop: Average')
      result.type = 'line'
      result.id =8
      $scope.graphs['anonymity'].push(result)
    })

    MetricService.get({id: $stateParams.id, metric: 'top_rank_by_hop.json'}).$promise.then(function (result) {
      result.options = basic_graph_options('Top Ranked Value by Intercepted at Hop: Average')
      result.type = 'line'
      result.id =9
      $scope.graphs['anonymity'].push(result)
    })

    $scope.open = function (index) {
      var modalInstance = $uibModal.open({
        animation: true,
        ariaLabelledBy: 'modal-title',
        ariaDescribedBy: 'modal-body',
        templateUrl: 'myModalContent.html',
        controller: 'ModalInstanceCtrl',
        controllerAs: '$ctrl',
        size: 'lg',
        resolve: {
          graph: function () {
            for (key in $scope.graphs){
              for (g in $scope.graphs[key]){
                if ($scope.graphs[key][g].id === index){
                  return $scope.graphs[key][g]
                }
              }
            }
            return null
          }
        }
      })
    }
  }).controller('ModalInstanceCtrl', function ($uibModalInstance, graph) {
  var $ctrl = this
  $ctrl.graph = graph
  $ctrl.ok = function () {
    $uibModalInstance.close()
  }
})
  .controller('MenuController', function ($scope, $state, ExperimentService) {
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
  }).controller('DataController', function ($scope, $state, $stateParams, DataService) {
  $scope.id = $stateParams.id
  $scope.filter_text = ''
  $scope.filtered_data = []
  $scope.on_filter = function () {
    $scope.filtered_data = {'status': 'Loading....'}
    DataService.query({id: $stateParams.id, filter: $scope.filter_text}).$promise.then(function (result) {
      $scope.filtered_data = result.items
    })
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

drag = simulation => {
    function dragstarted(d) {
      if (!d3.event.active) simulation.alphaTarget(0.3).restart();
      d.fx = d.x;
      d.fy = d.y;
    }
    
    function dragged(d) {
      d.fx = d3.event.x;
      d.fy = d3.event.y;
    }
    
    function dragended(d) {
      if (!d3.event.active) simulation.alphaTarget(0);
      d.fx = null;
      d.fy = null;
    }
    
    return d3.drag()
        .on("start", dragstarted)
        .on("drag", dragged)
        .on("end", dragended);
}

const graph = {{data}}
var nodes = graph["nodes"]
var links = graph["links"]

const nodetypes = Array.from(new Set(nodes.map(node => node.type)))
const linktypes = Array.from(new Set(links.map(link => link.type)))
const color = d3.scaleOrdinal(nodetypes.concat(linktypes),d3.schemeCategory10)

var height = 800, width = 800;

var svg = d3.select("svg")
  .attr("viewBox",  [-width / 2, -height / 2, width, height])

var simulation = d3.forceSimulation(nodes)
    .force("charge", d3.forceManyBody().strength(-400))
    .force("link", d3.forceLink(links).id(node => node.id).distance(50))
    .force("x", d3.forceX())
    .force("y", d3.forceY())
    .on("tick", ticked);

var link = svg.append("g")
    .attr("stroke-width", 1.5)
    .attr("class","links")
  .selectAll("line")  

var node = svg.append("g")  
    .attr("stroke-width", 1)
    .attr("stroke", "black")
    .attr("class", "nodes")
  .selectAll("g")

redraw();

$("document").ready(function() {
  $(".categorie").click(function() {
    nodes = []
    links = []
    if($("#Ressources").prop("checked")) {graph["nodes"].map(node => {if(node.type == "Ressource"){nodes.push(node);}})}
    if($("#SAEs").prop("checked")) {
      if (nodes.length != 0) {graph["links"].map(link => {if(link.type == "RessourceToSAE"){links.push(link);}})}
      nodes.concat(graph["nodes"].map(node => {if(node.type == "SAE"){nodes.push(node);}}));
    }
    if($("#ACs").prop("checked")) {
      if($("#Ressources").prop("checked")) {graph["links"].map(link => {if(link.type == "RessourceToAC"){links.push(link);}})}
      if($("#SAEs").prop("checked")) {graph["links"].map(link => {if(link.type == "SAEToAC"){links.push(link);}})}
      nodes.concat(graph["nodes"].map(node => {if(node.type == "AC"){nodes.push(node);}}));
    }
    redraw();
  });
});

function redraw() {

  link = link.data(links)
    .join("line")
    .attr("stroke", d => color(d.type));

  node.selectAll("text").remove();
  node.selectAll("rect").remove();

  node = node.data(nodes)
    .join("g")
      .attr("class","node")
      .call(drag(simulation))

  node.append("rect")
        .attr("width", 20)
        .attr("height", 10)
        .attr("x", -10)
        .attr("y", -5)
        .attr("rx", 5)
        .attr("ry", 5)
        .attr("fill", function(d) { return color(d.type); })

  node.append("text")
        .attr("style", "user-select: none")
        .text(d => d.id)
        .attr("dx", 7)
        .attr("dy", 12)

  simulation.nodes(nodes);
  simulation.force("links", d3.forceLink(links).id(node => node.id).distance(100));
  simulation.alpha(0.5).restart();
}

function ticked() {
  link.attr("x1", function(d) { return d.source.x; })
      .attr("y1", function(d) { return d.source.y; })
      .attr("x2", function(d) { return d.target.x; })
      .attr("y2", function(d) { return d.target.y; });
  node
    .attr("transform", d => `translate(${d.x},${d.y})`);
}

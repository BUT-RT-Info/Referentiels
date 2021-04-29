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
    
    redraw()

    simulation.nodes(nodes);
    simulation.force("links", d3.forceLink(links).id(node => node.id));
    simulation.alpha(1).restart();
  });
function redraw() {

  $(".nodes").children().remove();

  NODE.data(nodes)
    .remove()
    .enter().append("rect")
    .attr("width", 40)
    .attr("height", 20)
    .attr("x", -20)
    .attr("y", -10)
    .attr("rx", 5)
    .attr("ry", 5)
    .attr("fill", function(d) { return color(d.type); });
    
}
});

const nodetypes = Array.from(new Set(nodes.map(node => node.type)))
const linktypes = Array.from(new Set(links.map(link => link.type)))

const color = d3.scaleOrdinal(nodetypes.concat(linktypes),d3.schemeCategory10)

var height = 800, width = 800;

var svg = d3.select("svg")
  .attr("viewBox", [0, 0, width, height])

var simulation = d3.forceSimulation(nodes)
    .force("charge", d3.forceManyBody().strength(-400))
    .force("center", d3.forceCenter(width / 2, height / 2))
    .force("link", d3.forceLink(links).id(node => node.id));

var link = svg.append("g")
    .attr("stroke-width", 1.5)
    .attr("class","links")
  .selectAll("line")
    .data(links)
    .join("line")
      .attr("stroke", d => color(d.type));


var NODE = svg.append("g")  
    .attr("stroke-width", 1)
    .attr("stroke", "black")
    .attr("class","nodes")
  .selectAll("g")
    .data(nodes)
    .join("g")
      .call(drag(simulation));

NODE.append("rect")
  .attr("width", 40)
  .attr("height", 20)
  .attr("x", -20)
  .attr("y", -10)
  .attr("rx", 5)
  .attr("ry", 5)
  .attr("fill", function(d) { return color(d.type); });

NODE.append("text")
  .text(d => d.id)
  .attr("dx", 15)
  .attr("dy", 25)

simulation.on("tick", ticked);

function ticked() {
  link.attr("x1", function(d) { return d.source.x; })
      .attr("y1", function(d) { return d.source.y; })
      .attr("x2", function(d) { return d.target.x; })
      .attr("y2", function(d) { return d.target.y; });

  NODE
    .attr("transform", d => `translate(${d.x},${d.y})`);
}


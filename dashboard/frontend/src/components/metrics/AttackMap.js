import React, { useRef, useEffect, useState } from 'react';
import { Box, Typography, Paper, CircularProgress } from '@mui/material';
import * as d3 from 'd3';

const AttackMap = ({ alerts = [] }) => {
  const svgRef = useRef(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  const width = 800;
  const height = 500;
  const simulationRef = useRef(null);

  useEffect(() => {
    if (!svgRef.current) return;

    // Clear any existing content and reset state
    setIsLoading(true);
    setError(null);
    
    try {
      const svg = d3.select(svgRef.current);
      svg.selectAll('*').remove();

      if (!alerts || !Array.isArray(alerts) || alerts.length === 0) {
        setIsLoading(false);
        return;
      }

      // Group alerts by source IP
      const sourceIps = {};
      alerts.forEach(alert => {
        if (!alert || !alert.source) return;
        
        if (!sourceIps[alert.source]) {
          sourceIps[alert.source] = {
            count: 0,
            severity: { low: 0, medium: 0, high: 0, critical: 0 },
            types: {}
          };
        }
        
        sourceIps[alert.source].count++;
        const severity = alert.severity || 'low';
        sourceIps[alert.source].severity[severity] = 
          (sourceIps[alert.source].severity[severity] || 0) + 1;
        
        const type = alert.type || 'Unknown';
        sourceIps[alert.source].types[type] = (sourceIps[alert.source].types[type] || 0) + 1;
      });

      // Create nodes with validation
      const nodes = Object.entries(sourceIps)
        .filter(([_, data]) => data && data.count > 0)
        .map(([ip, data]) => ({
          id: ip,
          ...data,
          radius: 10 + Math.sqrt(data.count) * 2,
          x: Math.random() * width,
          y: Math.random() * height
        }));

      if (nodes.length === 0) {
        setIsLoading(false);
        return;
      }

      // Create links with validation
      const links = alerts
        .filter(alert => alert && alert.source && alert.destination)
        .map(alert => ({
          source: alert.source,
          target: alert.destination,
          value: ['high', 'critical'].includes(alert.severity) ? 2 : 1
        }))
        .filter(link => 
          nodes.some(n => n.id === link.source) && 
          nodes.some(n => n.id === link.target)
        );

      // Stop any existing simulation
      if (simulationRef.current) {
        simulationRef.current.stop();
      }

      // Create force simulation with error handling
      const simulation = d3.forceSimulation(nodes)
        .force('charge', d3.forceManyBody().strength(-100))
        .force('center', d3.forceCenter(width / 2, height / 2))
        .force('collision', d3.forceCollide().radius(d => d.radius + 5).strength(0.7))
        .force('link', d3.forceLink(links)
          .id(d => d.id)
          .distance(100)
          .strength(0.1)
        )
        .alphaDecay(0.05);

      // Draw links
      const link = svg.append('g')
        .selectAll('line')
        .data(links, d => `${d.source.id || d.source}-${d.target}`)
        .enter().append('line')
        .attr('stroke', '#555')
        .attr('stroke-opacity', 0.6)
        .attr('stroke-width', d => Math.sqrt(d.value) || 1);

      // Draw nodes
      const node = svg.append('g')
        .selectAll('g')
        .data(nodes, d => d.id)
        .enter().append('g')
        .call(
          d3.drag()
            .on('start', dragstarted)
            .on('drag', dragged)
            .on('end', dragended)
        );

      node.append('circle')
        .attr('r', d => d.radius || 10)
        .attr('fill', d => {
          try {
            const maxSev = Object.entries(d.severity || {})
              .reduce((a, b) => (b[1] > (a[1] || 0) ? b : a), ['low', 0]);
            return {
              'low': '#4caf50',
              'medium': '#ff9800',
              'high': '#f44336',
              'critical': '#9c27b0'
            }[maxSev[0]] || '#9e9e9e';
          } catch (e) {
            console.error('Error setting node color:', e);
            return '#9e9e9e';
          }
        })
        .attr('opacity', 0.8)
        .on('mouseover', function(event, d) {
          try {
            if (!d) return;
            d3.select(this).attr('stroke', '#fff').attr('stroke-width', 2);
            
            const tooltipHtml = `
              <div><strong>IP:</strong> ${d.id || 'Unknown'}</div>
              <div><strong>Alerts:</strong> ${d.count || 0}</div>
              <div><strong>Severity:</strong> ${Object.entries(d.severity || {})
                .filter(([_, v]) => v > 0)
                .map(([k, v]) => `${k}: ${v}`)
                .join(', ')}</div>
            `;
            
            tooltip.transition().duration(200).style('opacity', 0.9);
            tooltip.html(tooltipHtml)
              .style('left', `${event.pageX + 10}px`)
              .style('top', `${event.pageY - 28}px`);
          } catch (e) {
            console.error('Error in mouseover:', e);
          }
        })
        .on('mouseout', function() {
          d3.select(this).attr('stroke', 'none');
          tooltip.transition().duration(500).style('opacity', 0);
        });

      // Add IP labels
      node.append('text')
        .attr('dy', 4)
        .attr('text-anchor', 'middle')
        .text(d => {
          try {
            const parts = (d.id || '').split('.');
            return parts[parts.length - 1] || '?';
          } catch (e) {
            console.error('Error creating label:', e);
            return '?';
          }
        })
        .attr('fill', '#fff')
        .attr('font-size', '10px')
        .attr('pointer-events', 'none');

      // Tooltip
      const tooltip = d3.select('body').append('div')
        .attr('class', 'tooltip')
        .style('opacity', 0)
        .style('position', 'absolute')
        .style('background', 'rgba(0,0,0,0.8)')
        .style('padding', '8px')
        .style('border-radius', '4px')
        .style('color', 'white')
        .style('font-size', '12px')
        .style('pointer-events', 'none')
        .style('z-index', '1000');

      // Update positions on simulation tick
      simulation.on('tick', () => {
        try {
          link
            .attr('x1', d => d.source.x || 0)
            .attr('y1', d => d.source.y || 0)
            .attr('x2', d => (d.target && d.target.x) || 0)
            .attr('y2', d => (d.target && d.target.y) || 0);

          node.attr('transform', d => `translate(${d.x || 0},${d.y || 0})`);
        } catch (e) {
          console.error('Error in simulation tick:', e);
        }
      });

      // Drag functions with error handling
      function dragstarted(event, d) {
        try {
          if (!event.active) simulation.alphaTarget(0.3).restart();
          d.fx = d.x;
          d.fy = d.y;
        } catch (e) {
          console.error('Error in dragstarted:', e);
        }
      }

      function dragged(event, d) {
        try {
          d.fx = event.x;
          d.fy = event.y;
        } catch (e) {
          console.error('Error in dragged:', e);
        }
      }

      function dragended(event, d) {
        try {
          if (!event.active) simulation.alphaTarget(0);
          d.fx = null;
          d.fy = null;
        } catch (e) {
          console.error('Error in dragended:', e);
        }
      }

      // Store simulation reference for cleanup
      simulationRef.current = simulation;
      setIsLoading(false);
      
      // Cleanup function
      return () => {
        try {
          if (simulationRef.current) {
            simulationRef.current.stop();
            simulationRef.current = null;
          }
          d3.selectAll('.tooltip').remove();
        } catch (e) {
          console.error('Error during cleanup:', e);
        }
      };
    } catch (e) {
      console.error('Error initializing attack map:', e);
      setError('Failed to initialize attack map visualization.');
      setIsLoading(false);
      
      // Add error message to the SVG
      const svg = d3.select(svgRef.current);
      svg.append('text')
        .attr('x', width / 2)
        .attr('y', height / 2)
        .attr('text-anchor', 'middle')
        .attr('fill', '#ff4444')
        .text('Error loading attack map');
    }
  }, [alerts]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      try {
        if (simulationRef.current) {
          simulationRef.current.stop();
          simulationRef.current = null;
        }
        d3.selectAll('.tooltip').remove();
      } catch (e) {
        console.error('Error during unmount cleanup:', e);
      }
    };
  }, []);

  if (error) {
    return (
      <Paper elevation={3} sx={{ p: 2, height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <Typography color="error">{error}</Typography>
      </Paper>
    );
  }

  return (
    <Paper elevation={3} sx={{ p: 2, height: '100%', width: '100%', overflow: 'hidden' }}>
      <Typography variant="h6" gutterBottom>Network Attack Map</Typography>
      <Box 
        sx={{ 
          width: '100%', 
          height: 'calc(100% - 40px)', 
          overflow: 'auto',
          position: 'relative',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center'
        }}
      >
        {isLoading && (
          <Box 
            sx={{
              position: 'absolute',
              top: 0,
              left: 0,
              right: 0,
              bottom: 0,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              backgroundColor: 'rgba(0, 0, 0, 0.5)',
              zIndex: 10
            }}
          >
            <CircularProgress />
          </Box>
        )}
        <svg 
          ref={svgRef} 
          width={width} 
          height={height}
          style={{
            display: 'block',
            margin: '0 auto',
            backgroundColor: '#1e1e1e',
            borderRadius: '4px',
            minWidth: width,
            minHeight: height
          }}
          preserveAspectRatio="xMidYMid meet"
        />
        {!alerts.length && !isLoading && (
          <Box
            sx={{
              position: 'absolute',
              top: '50%',
              left: '50%',
              transform: 'translate(-50%, -50%)',
              textAlign: 'center',
              color: 'text.secondary'
            }}
          >
            <Typography>No alert data available</Typography>
          </Box>
        )}
      </Box>
    </Paper>
  );
};

export default AttackMap;

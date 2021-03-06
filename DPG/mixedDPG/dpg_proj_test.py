from dolfin import *
from numpy import array, argsort, amax
from math import ceil

import helper_functions as help
import helper_confusion as chelp

# Create mesh and definene function space
eps = float(help.parseArg('--eps',1e-2))
pU = int(help.parseArg('--p',1))
N = int(help.parseArg('--N',4))

useStrongBC = help.parseArg('--useStrongBC','False')=='True' #eval using strings
plotFlag = help.parseArg('--plot','True')=='True' #eval using strings

dp = int(help.parseArg('--dp',1))

pV = pU+dp
mesh = UnitSquareMesh(N,N)

# define problem params
print "eps = ", eps
beta = Expression(('1.0','0.0'))
ue = chelp.erikkson_solution(eps)
grad_ue = chelp.erikkson_solution_gradient(eps)

zero = Expression('0.0')

infl = chelp.Inflow()
outfl = 1-infl

# define spaces
U = FunctionSpace(mesh, "Lagrange", pU)
V = FunctionSpace(mesh, "Lagrange", pV)
E = U*V
(u,e) = TrialFunctions(E)
(du,v) = TestFunctions(E)
n = FacetNormal(mesh)
h = CellSize(mesh)

bcs = []
bcs.append(DirichletBC(E.sub(1), zero, chelp.outflow)) # error boundary condition
bcs.append(DirichletBC(E.sub(0), ue, chelp.inflow)) # boundary conditions on u
if useStrongBC:
	bcs.append(DirichletBC(E.sub(0), ue, chelp.outflow)) # boundary conditions on u

def ip(e,v):
	return inner(dot(beta,grad(e)),dot(beta,grad(v)))*dx + eps*inner(grad(e),grad(v))*dx #+ eps*inner(infl*e,v)*ds + eps*inner(outfl*dot(grad(e),n),dot(grad(v),n))*ds

def b(u,v):
	fieldForm = inner(dot(beta,n)*u,v)*ds + inner(-u,dot(beta,grad(v)))*dx + eps*inner(grad(u),grad(v))*dx 
	if useStrongBC: # strong outflow
		return fieldForm - inner(eps*dot(grad(u),n),v)*ds 
	else: # nitsche type of weak BC
		return fieldForm - inner(eps*dot(grad(u),n),v)*ds - inner(eps*outfl*u,dot(grad(v),n))*ds 

a = b(u,v) + b(du,e) + ip(e,v) #+ eps*inner(outfl*u,du)*ds

f = Expression('0.0')
x = V.cell().x
L = inner(f,v)*dx 

uSol = Function(E)
solve(a==L, uSol, bcs)
(u,e) = uSol.split()

	
fineMesh = chelp.quadrature_refine(mesh,N,numQRefs)
fineSpace = FunctionSpace(fineMesh, "Lagrange", pU+2)
uF = interpolate(u,fineSpace)
L2err = (ue-uF)**2*dx
l_err = sqrt(assemble(L2err))
hh = (1.0/N)*.5**float(refIndex)

print "on refinement ", refIndex
energy = ip(e,e)
totalE = sqrt(assemble(energy))

H1err = (grad_ue-grad(uF))**2*dx
edge_error = infl*1/h*(ue-uF)**2*ds
n_err = sqrt(assemble(eps*edge_error + eps*H1err + L2err))
nitscheErrVec.append(n_err)

print "h, ", hh , ", L2 error = ", l_err, ", e = ", totalE	

if plotFlag:
	# Plot solution
	fineMesh = mesh
	for ref in xrange(pU-1):
		fineMesh = refine(fineMesh)
		fineSpace = FunctionSpace(fineMesh, "Lagrange", 1)
	uF = interpolate(u, fineSpace)
	eF = interpolate(e, fineSpace)
	err = ue-uF
	plot(uF)
	plot(eF)
	plot(mesh)
	#plot(err)
	interactive()


#file = File('u.pvd')
#file << uF
#file = File('e.pvd')
#file << eF
#file = File('mesh.pvd')
#file << mesh

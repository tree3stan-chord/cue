module granular_mod
  implicit none
contains

  subroutine granular_synth(input, output, n, grain_size, hop_size)
    integer, intent(in) :: n, grain_size, hop_size
    real(8), intent(in) :: input(n)
    real(8), intent(out) :: output(n)
    real(8), allocatable :: window(:)
    integer :: i, start

    allocate(window(grain_size))
    do i = 1, grain_size
      window(i) = 0.5d0 * (1.0d0 - cos(2.0d0*3.141592653589793d0*(i-1)/(grain_size-1)))
    end do

    output = 0.0d0
    start = 1
    do while (start + grain_size - 1 <= n)
      do i = 1, grain_size
        output(start + i - 1) = output(start + i - 1) + input(start + i - 1) * window(i)
      end do
      start = start + hop_size
    end do

    deallocate(window)
  end subroutine granular_synth
  
end module granular_mod
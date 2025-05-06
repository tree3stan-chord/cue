module delay_mod
  implicit none
  real(8), allocatable, save :: buffer(:)
  integer, save :: buf_len = 0
  integer, save :: write_ptr = 0
contains

  subroutine delay(input, output, n, delay_samples, feedback)
    integer, intent(in) :: n, delay_samples
    real(8), intent(in) :: input(n), feedback
    real(8), intent(out) :: output(n)
    integer :: i, idx

    if (buf_len /= delay_samples) then
      if (allocated(buffer)) deallocate(buffer)
      allocate(buffer(delay_samples))
      buffer = 0.0d0
      buf_len = delay_samples
      write_ptr = 0
    end if
    
    do i = 1, n
      idx = mod(write_ptr, buf_len) + 1
      output(i) = input(i) + feedback * buffer(idx)
      buffer(idx) = output(i)
      write_ptr = mod(write_ptr + 1, buf_len)
    end do
  end subroutine delay
  
end module delay_mod